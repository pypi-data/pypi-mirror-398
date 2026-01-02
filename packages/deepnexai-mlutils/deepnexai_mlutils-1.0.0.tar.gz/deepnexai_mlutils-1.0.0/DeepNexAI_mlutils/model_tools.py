import tensorflow as tf
from tensorflow.keras.utils import plot_model
from PIL import Image, ImageDraw, ImageFont
import os

def get_mono_font(size=20):
    fonts = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for f in fonts:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def save_model_visualizer(model, model_name="Model"):

    # Architecture
    plot_model(model, f"{model_name}_Architecture.png", show_shapes=True, dpi=200)

    # Parameters
    total = model.count_params()
    trainable = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
    non_trainable = sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights)

    with open(f"{model_name}_Parameters.txt", "w") as f:
        f.write(f"Total: {total}\nTrainable: {trainable}\nNon-trainable: {non_trainable}")

    # Dark Summary
    summary_lines = []
    model.summary(print_fn=lambda x: summary_lines.append(x))

    font = get_mono_font()
    bg = (15, 15, 20)

    pad = 40
    spacing = 10

    dummy = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(dummy)

    def ts(t):
        box = d.textbbox((0,0), t, font)
        return box[2]-box[0], box[3]-box[1]

    width = max(ts(l)[0] for l in summary_lines) + pad*2
    height = sum(ts(l)[1] + spacing for l in summary_lines) + pad*2

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    y = pad
    for line in summary_lines:
        draw.text((pad, y), line, fill=(230,230,230), font=font)
        y += ts(line)[1] + spacing

    img.save(f"{model_name}_Summary.png", dpi=(300,300))
