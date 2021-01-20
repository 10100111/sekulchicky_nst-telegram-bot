from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
import os


def get_number_of_styles(model_folder="/models"):
    DIR = f"{os.getcwd()}{model_folder}"
    n_styles = len([name for name in os.listdir(DIR) if
                    os.path.isfile(os.path.join(DIR, name))])
    return n_styles

