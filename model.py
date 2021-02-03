import torch
import transformernet
from torchvision import transforms
from PIL import Image
import utils
import io


class StyleModel:

    def __init__(self, model_id, device='cpu'):
        self.model_id = model_id
        self.device = device
        self.model = transformernet.TransformerNet()
        for param in self.model.parameters():
            param.requires_grad = False

    def load_model(self):
        model_path = utils.get_model_path(self.model_id)
        state_dict = torch.load(model_path)
        self.model.load_state_dict(state_dict, strict=False)

    def run(self, image):
        with torch.no_grad():
            image = self.preprocess(image)
            self.model.to(self.device)
            result = self.model(image).cpu()
            return self.postprocess(result[0])

    def preprocess(self, image):
        size = 1500
        if max(image.size) > size:
            transform = transforms.Compose([
                transforms.Resize(size),
                transforms.CenterCrop(size),
                transforms.ToTensor(),
                transforms.Lambda(lambda x: x.mul(255))])
        else:
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Lambda(lambda x: x.mul(255))])
        image = transform(image)

        return image.unsqueeze(0).to(self.device)

    def postprocess(self, data):
        img = data.clone().clamp(0, 255).numpy()
        img = img.transpose(1, 2, 0).astype("uint8")
        img = Image.fromarray(img)
        bio = io.BytesIO()
        bio.name = f'{self.model_id}_output.jpeg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
