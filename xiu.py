from PIL import Image

def make_background_transparent(image_path, output_path):
    """
    将图片的背景色变为透明。

    参数:
    image_path (str): 输入图片的路径。
    output_path (str): 处理后图片的保存路径。
    """
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {image_path}")
        return

    # 将图片转换为RGBA格式，这样才有Alpha（透明度）通道
    img = img.convert("RGBA")

    datas = img.getdata()

    new_data = []
    # 获取背景色 (假设是左上角第一个像素的颜色)
    # 如果你的背景色不是这个，你需要手动指定背景色
    # 例如: background_color = (255, 255, 255, 255) # 白色
    background_color = datas[0]
    print(f"检测到的背景色为: {background_color}")

    for item in datas:
        # 如果像素颜色与背景色相同，则将其变为完全透明
        if item[0] == background_color[0] and \
           item[1] == background_color[1] and \
           item[2] == background_color[2] and \
           (len(item) < 4 or item[3] == background_color[3]): # 检查Alpha值（如果存在）
            new_data.append((255, 255, 255, 0))  # RGBA, A=0表示完全透明
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"成功将背景透明化后的图片保存到: {output_path}")

# --- 使用方法 ---
# 1. 确保你已经安装了 Pillow 库:
#    pip install Pillow

# 2. 替换下面的 'your_sprite_sheet.png' 为你的图片文件名
#    并将 'output_transparent_sprite_sheet.png' 替换为你希望保存的文件名
input_image_file = './assets/Guali/upwards.png'  # 假设你的图片文件名为 upwards.png
output_image_file = './assets/Guali/upwards_transparent.png'

make_background_transparent(input_image_file, output_image_file)