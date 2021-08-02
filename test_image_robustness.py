import numpy as np 
import cv2
import matplotlib.pyplot as plt
import torch 
from torch import nn
from models import *

SIZE = 256

def pred2img(pred):
    pred = pred.detach().cpu().numpy()
    pred = np.clip(pred, 0.0, 1.0)
    pred = (pred * 255.0).astype(np.uint8)
    pred = pred.reshape((SIZE,SIZE,3))
    return pred

image = cv2.imread("test.jpg")
image = cv2.resize(image, (SIZE,SIZE)).astype(np.float32) / 255.0
image_origin = image
image = image + np.random.normal(loc=0, scale=0.1, size=np.shape(image))
image = np.clip(image, 0, 1)
cv2.imshow("original", (image_origin * 255.0).astype(np.byte))
cv2.imshow("target", (image * 255.0).astype(np.byte))

# generate the target data of training
# image_torch = torch.from_numpy(image.astype(np.float32)/255.0)
image_torch = torch.from_numpy(image)
image_origin_torch = torch.from_numpy(image_origin)
# image_torch += 0.1 * torch.randn(image_torch.size())
image_torch = image_torch.view(-1,3).cuda()
image_origin_torch = image_origin_torch.view(-1, 3).cuda()

# generate input image grids
xs, ys = np.meshgrid(np.linspace(-1,1,SIZE), np.linspace(-1,1,SIZE))
# xs, ys = np.meshgrid(np.linspace(0,511,512), np.linspace(0,511,512))
xs = torch.from_numpy(xs.astype(np.float32)).view(SIZE,SIZE,1)
ys = torch.from_numpy(ys.astype(np.float32)).view(SIZE,SIZE,1)
input_grid = torch.cat([ys, xs],dim=2)
input_grid = input_grid.view(-1,2)
input_grid = input_grid.cuda()

# initialize the models
relu_model = ReLU_Model([2,256,256,256,256,3]).cuda()
relu_pe_model = ReLU_PE_Model([2,256,256,256,256,3], L=10).cuda()
siren_model = SIREN([2,256,256,256,256,3]).cuda()

# initialize the optimizer
parameters = []
parameters += list(relu_model.parameters())
parameters += list(relu_pe_model.parameters())
parameters += list(siren_model.parameters())
optimizer = torch.optim.Adam(parameters, lr=1e-4)

loss_log = []
print("press ESC on any img to quit reconstruction")
for iter_idx in range(10000):
    relu_recon = relu_model(input_grid)
    relu_pe_recon = relu_pe_model(input_grid)
    siren_recon = siren_model(input_grid)

    relu_loss = torch.mean((relu_recon - image_torch)**2)
    relu_pe_loss = torch.mean((relu_pe_recon - image_torch)**2)
    siren_loss = torch.mean((siren_recon - image_torch)**2)
    relu_loss_origin = torch.mean((relu_recon - image_origin_torch)**2)
    relu_pe_loss_origin = torch.mean((relu_pe_recon - image_origin_torch)**2)
    siren_loss_origin = torch.mean((siren_recon - image_origin_torch)**2)
    total_loss = relu_loss + relu_pe_loss + siren_loss

    optimizer.zero_grad()
    total_loss.backward()
    optimizer.step()

    loss_log.append({
        "relu_loss": relu_loss.item(),
        "relu_pe_loss": relu_pe_loss.item(),
        "siren_loss": siren_loss.item(),
        "relu_origin_loss": relu_loss_origin.item(),
        "relu_pe_origin_loss": relu_pe_loss_origin.item(),
        "siren_origin_loss": siren_loss_origin.item()
    })

    if iter_idx % 100 == 0:
        log_str = "relu loss: %f, relu pe loss: %f, siren loss: %f" % (
            relu_loss.item(), relu_pe_loss.item(), siren_loss.item())
        print(log_str)
        relu_img = pred2img(relu_recon)
        relu_pe_img = pred2img(relu_pe_recon)
        siren_img = pred2img(siren_recon)
        big_img = np.concatenate([relu_img, relu_pe_img, siren_img], axis=1)
        cv2.imshow("reconstructed img", big_img)
        if cv2.waitKey(10) == 27:
            break

relu_losses = [i["relu_loss"] for i in loss_log]
relu_pe_losses = [i["relu_pe_loss"] for i in loss_log]
siren_losses = [i["siren_loss"] for i in loss_log]

step_num = len(loss_log)
plt.plot(range(step_num), relu_losses, label='relu_losses')
plt.plot(range(step_num), relu_pe_losses, label='relu_pe_losses')
plt.plot(range(step_num), siren_losses, label='siren_losses')
plt.legend(loc='upper right')
plt.show()

relu_losses = [i["relu_origin_loss"] for i in loss_log]
relu_pe_losses = [i["relu_pe_origin_loss"] for i in loss_log]
siren_losses = [i["siren_origin_loss"] for i in loss_log]

step_num = len(loss_log)
plt.plot(range(step_num), relu_losses, label='relu_origin_losses')
plt.plot(range(step_num), relu_pe_losses, label='relu_pe_origin_losses')
plt.plot(range(step_num), siren_losses, label='siren_origin_losses')
plt.legend(loc='upper right')
plt.show()

