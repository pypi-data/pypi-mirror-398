import tensorflow as tf
from tensorflow.keras.utils import plot_model
from PIL import Image, ImageDraw, ImageFont
import os

# ===== Cross-Platform Mono Font =====
def get_mono_font(size=20):
    possible_fonts = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for f in possible_fonts:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()

# ===== Save model architecture, parameters, and dark summary =====
def save_model_visualizer(model, model_name="Model", output_dir="model_outputs"):
    # Create output folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # ===== Architecture Graph (PNG + SVG) =====
    plot_model(
        model,
        to_file=os.path.join(output_dir, f"{model_name}_Architecture.png"),
        show_shapes=True,
        show_layer_names=True,
        expand_nested=True,
        dpi=200
    )
    try:
        plot_model(
            model,
            to_file=os.path.join(output_dir, f"{model_name}_Architecture.svg"),
            show_shapes=True,
            show_layer_names=True,
            expand_nested=True,
            dpi=200
        )
    except Exception as e:
        print(f"⚠️ SVG output not generated: {e}")

    # ===== Parameters TXT =====
    total = model.count_params()
    trainable = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
    non_trainable = sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights)
    with open(os.path.join(output_dir, f"{model_name}_Parameters.txt"), "w") as f:
        f.write(f"Total Params: {total}\nTrainable: {trainable}\nNon-Trainable: {non_trainable}\n")

    # ===== Dark Summary Image (PNG) =====
    summary_lines = []
    model.summary(print_fn=lambda x: summary_lines.append(x))
    font = get_mono_font(20)

    bg = (15, 15, 20)
    conv_color = (255, 140, 0)
    dense_color = (0, 200, 255)
    other_color = (180, 180, 180)

    def colorize(line):
        if "Conv" in line: return conv_color
        if "Dense" in line: return dense_color
        return other_color

    pad_x, pad_y = 40, 40
    line_spacing = 10
    dummy = Image.new("RGB", (10,10))
    draw_dummy = ImageDraw.Draw(dummy)

    def text_size(text):
        box = draw_dummy.textbbox((0,0), text, font=font)
        return box[2]-box[0], box[3]-box[1]

    width = max(text_size(l)[0] for l in summary_lines) + pad_x*2
    height = sum(text_size(l)[1] + line_spacing for l in summary_lines) + pad_y*2
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    y = pad_y
    for line in summary_lines:
        draw.text((pad_x, y), line, font=font, fill=colorize(line))
        y += text_size(line)[1] + line_spacing

    img.save(os.path.join(output_dir, f"{model_name}_Summary.png"), dpi=(300,300))
    print(f"✅ All files saved in: {output_dir}")
