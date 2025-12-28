import requests,os
from io import BytesIO
from PIL import Image




# ---------------------------------------------------------------------
# IMAGE VALIDATION (fetch + Pillow)
# ---------------------------------------------------------------------
def validate_image(image_url: str):
    """
    Downloads an image, validates size and format,
    returns a Pillow Image object or False.
    """
    try:
        # Request image
        resp = requests.get(image_url, timeout=5)
        if resp.status_code != 200:
            return False

        buffer = resp.content

        # 5MB limit (same as your TS version)
        if len(buffer) > 5 * 1024 * 1024:
            return False

        # Load image with Pillow
        img = Image.open(BytesIO(buffer))

        # Validate format
        fmt = (img.format or "").lower()
        if fmt not in ["jpg", "jpeg", "png", "webp", "gif"]:
            return False

        return img

    except Exception:
        return False


# ---------------------------------------------------------------------
# RESIZE IMAGE (Pillow equivalent of Sharp resize+crop)
# ---------------------------------------------------------------------
def crop_image(img: Image.Image,
                 target_width: int = 1200,
                 target_height: int = 627) -> Image.Image:
    
    width, height = img.size
    if width == target_width and height == target_height:
        return img
    target_ratio = target_width / target_height
    current_ratio = width / height

    # Determine scaling
    if current_ratio > target_ratio:
        # Wider than target — match height
        new_height = target_height
        new_width = int(new_height * current_ratio)
    else:
        # Taller than target — match width
        new_width = target_width
        new_height = int(new_width / current_ratio)

    # Resize
    resized = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Crop center to target size
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2

    cropped = resized.crop((
        left,
        top,
        left + target_width,
        top + target_height
    ))

    return cropped
def get_sized_image_path(file_path,height,width):
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    filename,ext = os.path.splitext(basename)
    file_spl = filename.split('_')
    potential_sizes = file_spl[-1].split('x')
    if len(potential_sizes) == 2 and False not in [is_number(size) for size in potential_sizes]:
        filename = file_spl[0]
    nufilename = f"{filename}_{height}x{width}"
    nubasename = f"{nufilename}{ext}"
    return os.path.join(dirname,nubasename)
def save_image_size_file(img,file_path):
    img.save(file_path)
    return file_path


def resize_image(img, target_width, target_height, fill_color=(0,0,0,0)):
    """
    Resize WITHOUT CROPPING, preserving aspect ratio,
    then pad to target_width × target_height.
    """
    ow, oh = img.size

    # compute scale to fit inside target
    scale = min(target_width / ow, target_height / oh)

    new_w = int(ow * scale)
    new_h = int(oh * scale)

    # Resize while keeping aspect ratio
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Create final canvas
    final = Image.new("RGBA", (target_width, target_height), fill_color)

    # center image on canvas
    paste_x = (target_width - new_w) // 2
    paste_y = (target_height - new_h) // 2

    final.paste(resized, (paste_x, paste_y))

    return final

def get_resized_image_file_path(
    file_path,
    img=None,
    target_width=None,
    target_height=None,
    save_resize=True,
    check_resize=True,
):

    target_width = target_width or 1200
    target_height = target_height or 627

    if not file_path and not img:
        return None

    sized_image_path = get_sized_image_path(file_path, target_height, target_width)

    if check_resize and os.path.isfile(sized_image_path):
        return sized_image_path

    img = img or Image.open(file_path)

    resized_image = resize_image(
        img=img,
        target_width=target_width,
        target_height=target_height,
    )

    if save_resize:
        save_image_size_file(resized_image, sized_image_path)

    return sized_image_path
