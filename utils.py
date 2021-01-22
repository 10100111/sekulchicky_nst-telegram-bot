from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
import os


def load_image(filename, size=None):
    img = Image.open(filename).convert('RGB')

    if max(img.size) > 2048:
        transform = transforms.Compose([
            transforms.Resize(size),
            transforms.CenterCrop(size),
            transforms.ToTensor(),
            transforms.Lambda(lambda x: x.mul(255))])
    else:
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Lambda(lambda x: x.mul(255))])
    img = transform(img)

    return img


def save_image(filename, data):
    img = data.clone().clamp(0, 255).numpy()
    img = img.transpose(1, 2, 0).astype("uint8")
    img = Image.fromarray(img)
    img.save(filename)


def gram_matrix(y):
    (b, ch, h, w) = y.size()
    features = y.view(b, ch, w * h)
    features_t = features.transpose(1, 2)
    gram = features.bmm(features_t) / (ch * h * w)
    return gram


def normalize_batch(batch):
    # normalize using imagenet mean and std
    mean = batch.new_tensor([0.485, 0.456, 0.406]).view(-1, 1, 1)
    std = batch.new_tensor([0.229, 0.224, 0.225]).view(-1, 1, 1)
    batch = batch.div_(255.0)
    return (batch - mean) / std


def imshow(tensor, title=None, ax_plt=None):
    # функция для отрисовки изображения
    image = tensor.cpu().clone().clamp(0, 255).numpy()
    image = image.transpose(1, 2, 0).astype("uint8")
    image = Image.fromarray(image)
    if ax_plt is not None:
        ax_plt.imshow(image)
        if title is not None:
            ax_plt.set_title(title)
    else:
        plt.imshow(image)
        if title is not None:
            plt.title(title)


def get_number_of_styles(model_folder="/models"):
    DIR = f"{os.getcwd()}{model_folder}"
    n_styles = len([name for name in os.listdir(DIR) if
                    os.path.isfile(os.path.join(DIR, name))])
    return n_styles


def get_model_path(model_id, model_folder="/models"):
    DIR = f"{os.getcwd()}{model_folder}"
    models = [name for name in os.listdir(DIR) if
              os.path.isfile(os.path.join(DIR, name))]
    return f"{DIR}/{models[model_id-1]}"
