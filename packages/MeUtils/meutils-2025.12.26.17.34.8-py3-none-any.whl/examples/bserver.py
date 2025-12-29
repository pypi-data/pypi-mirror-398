from PIL import Image
import os
import math


def stitch_images_grid(image_paths, output_path, cols, background_color=(255, 255, 255)):
    """
    使用 Pillow 将图片拼接成网格。
    假设所有图片大小相似，或以最大图片的尺寸为单元格大小。

    Args:
        image_paths (list): 包含图片文件路径的列表。
        output_path (str): 输出拼接后图片的路径。
        cols (int): 网格的列数。
        background_color (tuple): 画布背景色 (R, G, B)。
    """
    images = []
    max_w = 0
    max_h = 0

    # 加载图片并找到最大尺寸
    for path in image_paths:
        try:
            img = Image.open(path).convert('RGB')
            images.append(img)
            max_w = max(max_w, img.width)
            max_h = max(max_h, img.height)
        except FileNotFoundError:
            print(f"警告: 文件未找到 {path}, 跳过此图片。")
        except Exception as e:
            print(f"警告: 加载图片 {path} 时出错: {e}, 跳过此图片。")

    if not images:
        print("错误: 没有可拼接的有效图片。")
        return

    num_images = len(images)
    rows = math.ceil(num_images / cols)

    # 计算画布总尺寸
    grid_width = cols * max_w
    grid_height = rows * max_h

    # 创建画布
    grid_image = Image.new('RGB', (grid_width, grid_height), background_color)

    # 拼接图片到网格
    for index, img in enumerate(images):
        row = index // cols
        col = index % cols
        # 计算粘贴位置 (左上角)
        paste_x = col * max_w
        paste_y = row * max_h

        # 可选：如果图片尺寸小于单元格，可以居中
        offset_x = (max_w - img.width) // 2
        offset_y = (max_h - img.height) // 2

        grid_image.paste(img, (paste_x + offset_x, paste_y + offset_y))

    # 保存结果
    try:
        grid_image.save(output_path)
        print(f"图片已成功按 {rows}x{cols} 网格拼接并保存至: {output_path}")
    except Exception as e:
        print(f"错误: 保存网格图片时出错: {e}")


if __name__ == '__main__':

    # --- 示例用法 ---
    image_files = ["cover.jpeg", "image2.png", "image3.jpg", "image4.gif"]  # 替换路径
    image_files = ['cover.jpeg', 'img.png']
    output_file = "xxxxxxxxxxxxxxxxxxxxxxxxxxx.jpg"
    columns = 2  # 设置网格列数

    # (确保示例图片存在或创建它们)
    # if not os.path.exists("image4.gif"):
    #     try:
    #         img = Image.new('RGB', (110, 130), color = (50, 150, 50))
    #         img.save("image4.gif")
    #         print("创建了示例图片: image4.gif")
    #     except Exception as e:
    #          print(f"无法创建示例图片 image4.gif: {e}")


    stitch_images_grid(image_files, output_file, cols=columns)
