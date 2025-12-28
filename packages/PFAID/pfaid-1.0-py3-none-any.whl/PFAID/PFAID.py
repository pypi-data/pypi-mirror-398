from PIL import Image
import zlib
import struct


# --- Color Space Conversion (RGB <-> YCoCg) ---

def _rgb_to_ycocg(r, g, b):
    """Converts RGB to YCoCg-t (t-channel is the difference: R-B)."""
    t = r - b
    Co = g - b
    # Y = B + (R-B)/2 + (G-B)/2, using bit-shifts for division
    Y = b + (t >> 1) + (Co >> 1)
    return Y, Co, t


def _ycocg_to_rgb(Y, Co, t):
    """Converts YCoCg-t back to RGB."""
    # B = Y - Co/2 - t/2
    B = Y - (Co >> 1) - (t >> 1)
    G = Co + B
    R = t + B
    # Use modulo 256 to wrap around any values that exceeded 255 or went below 0
    return R % 256, G % 256, B % 256


# --- Predictors (Predictive Coding) ---

def _predict_sub(current, left):
    """Calculates residual using the 'Sub' predictor (current - left)."""
    return (current - left) % 256


def _reconstruct_sub(residual, left):
    """Reconstructs value using the 'Sub' predictor (residual + left)."""
    return (residual + left) % 256


def _locoi_med_predictor(left, above, up_left):
    """Calculates the LOCO-I MED predictor value."""
    if up_left >= max(left, above):
        predictor = min(left, above)
    elif up_left <= min(left, above):
        predictor = max(left, above)
    else:
        # Standard MED: P = Left + Above - UpLeft
        predictor = left + above - up_left
    return predictor % 256


def _predict_locoi(current, left, above, up_left):
    """Calculates residual using the LOCO-I MED predictor."""
    predictor = _locoi_med_predictor(left, above, up_left)
    return (current - predictor) % 256


def _reconstruct_locoi(residual, left, above, up_left):
    """Reconstructs value using the LOCO-I MED predictor."""
    predictor = _locoi_med_predictor(left, above, up_left)
    return (residual + predictor) % 256


# --- Decompression/Decoding ---

def Process_PFAID(PFAID, mode=0, pred_mode=0, cs_mode=0, PFAIDTYPE=0):
    """
    Decodes PFAID data (Pixels From All-In-One Data) into an RGB pixel list.
    mode 0: Data is compressed with zlib.
    pred_mode 0: LOCO-I prediction, 1: Sub predictor.
    cs_mode 0: YCoCg-t color space, 1: RGB color space.
    """
    if mode == 0:
        PFAID = zlib.decompress(PFAID)
    if PFAIDTYPE == 0:
        PIXEL_CHUNK_SIZE = 3

        DIMENSION_BYTES = 8
        # Last 8 bytes are dimensions (4 bytes width, 4 bytes height)
        dimension_bytes = PFAID[-DIMENSION_BYTES:]
        residual_data = PFAID[:-DIMENSION_BYTES]

        width_val = struct.unpack('>I', dimension_bytes[0:4])[0]
        height_val = struct.unpack('>I', dimension_bytes[4:8])[0]

        if len(residual_data) % PIXEL_CHUNK_SIZE != 0:
            print("Warning: Residual data length is not a multiple of 3. Data may be incomplete.")

        pixels = []
        # Store the reconstructed components (Y, Co, t or R, G, B) for the previous row
        prev_row_yco_a = [(0, 0, 0)] * width_val
        L = len(residual_data)
        C = PIXEL_CHUNK_SIZE

        # Store the reconstructed components (Y, Co, t or R, G, B) for the left pixel
        left_a, left_b, left_c = 0, 0, 0

        for i in range(0, L, C):
            pixel_index = i // C
            x = pixel_index % width_val
            y = pixel_index // width_val

            # Get 'Above' and 'Up-Left' components from the previous row
            above_a, above_b, above_c = prev_row_yco_a[x]
            up_left_a, up_left_b, up_left_c = prev_row_yco_a[x - 1] if x > 0 else (0, 0, 0)

            # Get residual data
            res_a = residual_data[i + 0]
            res_b = residual_data[i + 1]
            res_c = residual_data[i + 2]

            # Reconstruction based on pred_mode
            if pred_mode == 0:
                a = _reconstruct_locoi(res_a, left_a, above_a, up_left_a)
                b = _reconstruct_locoi(res_b, left_b, above_b, up_left_b)
                c = _reconstruct_locoi(res_c, left_c, above_c, up_left_c)
            elif pred_mode == 1:
                a = _reconstruct_sub(res_a, left_a)
                b = _reconstruct_sub(res_b, left_b)
                c = _reconstruct_sub(res_c, left_c)
            else:
                raise ValueError("Unknown PRED_MODE for decoding.")

            # Update 'Left' and 'Above' components for the next iteration
            left_a, left_b, left_c = a, b, c
            prev_row_yco_a[x] = (a, b, c)

            # Color space conversion based on cs_mode
            if cs_mode == 0:
                r, g, b = _ycocg_to_rgb(a, b, c)
            elif cs_mode == 1:
                r, g, b = a, b, c
            else:
                raise ValueError("Unknown CS_MODE for decoding.")

            pixels.append((r, g, b))

            # Reset 'Left' values at the start of a new row
            if (x + 1) == width_val:
                left_a, left_b, left_c = 0, 0, 0

        # Append dimensions to the end of the pixel list for convenience
        pixels.append(width_val)
        pixels.append(height_val)
        return pixels
    if PFAIDTYPE == 1:
        PIXEL_CHUNK_SIZE = 9
        rgb_stream_str = PFAID[:-18]
        if len(rgb_stream_str) % PIXEL_CHUNK_SIZE != 0:
            print("Warning: Input number length is not a multiple of 9. Data may be incomplete.")
        pixels = []
        L = len(rgb_stream_str)
        C = PIXEL_CHUNK_SIZE
        for k, i in enumerate(range(0, L, C)):
            s = rgb_stream_str[i: i + C]
            pixels.append((int(s[0:3]), int(s[3:6]), int(s[6:9])))
        pixels.append(int(PFAID[-18:-9]))
        pixels.append(int(PFAID[-9:]))
        return pixels
    # --- Compression/Encoding ---


def _get_raw_image_data(image_path, mode=0, pred_mode=0, cs_mode=0):
    """
    Reads an image, processes it (color space, prediction), and returns the PFAID payload.
    mode 0: Output is compressed with zlib.
    pred_mode 0: LOCO-I prediction, 1: Sub predictor.
    cs_mode 0: YCoCg-t color space, 1: RGB color space.
    """
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size
        print(f"Reading image: {image_path} (Width: {width}, Height: {height})")
        raw_pixel_data = img.tobytes()
        residual_data = bytearray()
        # Store the current row's component values (Y, Co, t or R, G, B)
        prev_row_yco_a = [(0, 0, 0)] * width

        # Store the 'Left' components
        left_a, left_b, left_c = 0, 0, 0

        for i in range(0, len(raw_pixel_data), 3):
            r_act = raw_pixel_data[i]
            g_act = raw_pixel_data[i + 1]
            b_act = raw_pixel_data[i + 2]

            pixel_index = i // 3
            x = pixel_index % width
            y = pixel_index // width

            # Color space conversion
            if cs_mode == 0:
                a_act, b_act, c_act = _rgb_to_ycocg(r_act, g_act, b_act)
            elif cs_mode == 1:
                a_act, b_act, c_act = r_act, g_act, b_act
            else:
                raise ValueError("Unknown CS_MODE for encoding.")

            # Get 'Above' and 'Up-Left' components
            above_a, above_b, above_c = prev_row_yco_a[x]
            up_left_a, up_left_b, up_left_c = prev_row_yco_a[x - 1] if x > 0 else (0, 0, 0)

            # Prediction based on pred_mode
            if pred_mode == 0:
                res_a = _predict_locoi(a_act, left_a, above_a, up_left_a)
                res_b = _predict_locoi(b_act, left_b, above_b, up_left_b)
                res_c = _predict_locoi(c_act, left_c, above_c, up_left_c)
            elif pred_mode == 1:
                res_a = _predict_sub(a_act, left_a)
                res_b = _predict_sub(b_act, left_b)
                res_c = _predict_sub(c_act, left_c)
            else:
                raise ValueError("Unknown PRED_MODE for encoding.")

            # Append residual to data stream
            residual_data.extend([res_a, res_b, res_c])

            # Update 'Left' and 'Above' components for the next iteration
            left_a, left_b, left_c = a_act, b_act, c_act
            prev_row_yco_a[x] = (a_act, b_act, c_act)

            # Reset 'Left' values at the start of a new row
            if (x + 1) == width:
                left_a, left_b, left_c = 0, 0, 0

        # Pack dimensions (Big Endian)
        width_bytes = width.to_bytes(4, byteorder='big')
        height_bytes = height.to_bytes(4, byteorder='big')
        pfaid_payload = bytes(residual_data) + width_bytes + height_bytes

        if mode == 0:
            return zlib.compress(pfaid_payload)
        if mode == 1:
            return pfaid_payload

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


# --- Image Output ---

def create_image_from_pixels(processed_PFAID, output_path="reconstructed_image.png"):
    """
    Creates and saves an image from a list of RGB tuples and dimensions.
    The list must contain (R, G, B) tuples followed by width and height as the last two elements.
    """
    total_pixels = len(processed_PFAID) - 2
    width, height = processed_PFAID[-2], processed_PFAID[-1]

    if width * height != total_pixels:
        raise ValueError(
            f"Dimension mismatch! Given WxH ({width}x{height} = {width * height}) "
            f"does not match the total number of pixels ({total_pixels}).")

    img = Image.new('RGB', (width, height))
    # img.putdata takes the list of (R, G, B) tuples
    img.putdata(processed_PFAID[:-2])
    img.save(output_path)
    print(f"\nImage successfully reconstructed and saved to: {output_path} (WxH: {width}x{height}) 🎉")


def read_image_pixels(image_path, mode=0, bytesmode=0, pred_mode=0, cs_mode=0):
    """
    Main function for image encoding.
    bytesmode 0: Returns PFAID raw bytes (residual + dimensions).
    bytesmode 1: Returns legacy hash string (not used for the main codec logic).
    """
    # bytesmode 0 triggers the main PFAID encoding logic
    if bytesmode == 0:
        return _get_raw_image_data(image_path, mode, pred_mode, cs_mode)

    # Legacy hash string generation (bytesmode 1)
    if bytesmode == 1:
        try:
            img_hash = []
            img = Image.open(image_path)
            img = img.convert("RGB")
            width, height = img.size
            print(f"Reading image: {image_path} (Width: {width}, Height: {height})")
            for y in range(height):
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    # Format each component as a 3-digit string (e.g., 255 -> "255")
                    img_hash.append(f"{r:03d}" + f"{g:03d}" + f"{b:03d}")

            # Append dimensions, formatted as 9-digit strings
            img_hash.append(f"{width:09d}" + f"{height:09d}")

            payload = "".join(img_hash)
            if mode == 0:
                return zlib.compress(payload.encode('utf-8'))
            if mode == 1:
                return payload

        except FileNotFoundError:
            print(f"Error: Image file not found at {image_path}")
        except Exception as e:
            print(f"An error occurred: {e}")