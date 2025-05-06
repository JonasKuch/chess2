import h5py
import torch
from torch import nn
from torchsummary import summary
from torch.utils.data import DataLoader
from torch.nn.utils import clip_grad_norm_
from chess2.bot import ChessDataset
from chess2.bot import NeuralNetwork


# Hyperparameters
BATCH_SIZE = 64
EPOCHS = 25 #150
LEARNING_RATE = 1e-3 #1e-4 was good
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 5


train_data = ChessDataset("src/chess2/bot/data/training_data.h5")
validation_data = ChessDataset("src/chess2/bot/data/validation_data.h5")
test_data = ChessDataset("src/chess2/bot/data/testing_data.h5")

train_dataloader = DataLoader(train_data, 64, shuffle=True, num_workers=NUM_WORKERS)
validation_dataloader = DataLoader(validation_data, 64, shuffle=True, num_workers=NUM_WORKERS)
test_dataloader = DataLoader(test_data, 64, shuffle=True, num_workers=NUM_WORKERS)


device = torch.device("cpu")
model = NeuralNetwork().to(device)


loss_policy = nn.CrossEntropyLoss(reduction="none")
loss_val = nn.MSELoss(reduction="none")


optimizer = torch.optim.Adam(
    params=model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY
)


scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="min",
    factor=0.5,
    patience=3
)

def sample_weights_func(depth):
    '''
    function form: w(x) = 1/( 1 + e^(-(x-m)/s) )

    find m and s by solving:
    w(20) = 0.5         --> min depth = 20
    w(100) = 0.99       --> max_depth = 100

    --> s = 17.14
    --> m = 20
    '''

    m = 20
    s = 17.14

    d = depth.float()

    return 1/(1+torch.exp(-(d-m)/s))


def train_loop(dataloader, model, loss_policy, loss_val, optimizer):
    size = len(dataloader.dataset)

    # Set the model to training mode - important for batch normalization and dropout layers
    model.train()

    for batch, (in_tensor, move_tgt, val_tgt, depth, moves_mask) in enumerate(dataloader):
        move_tgt = move_tgt.argmax(dim=1).long() # since crossentropyloss takes an index (label) as argument
        move_pred, val_pred = model(in_tensor)
        move_pred = move_pred.masked_fill(~moves_mask.bool(), -1e9)

        optimizer.zero_grad()

        sample_weights = sample_weights_func(depth)
        loss = ((loss_policy(move_pred, move_tgt) + loss_val(val_pred, val_tgt)) * sample_weights).mean()

        loss.backward()
        clip_grad_norm_(model.parameters(), max_norm=1)
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * BATCH_SIZE
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

        
def validation_loop(dataloader, model, loss_policy, loss_val):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    validation_loss, correct = 0, 0

    # Set the model in evaluation mode
    model.eval()

    # no_grad to suppress gradient computation
    with torch.no_grad():
        for (in_tensor, move_tgt, val_tgt, depth, moves_mask) in dataloader:
            move_tgt = move_tgt.argmax(dim=1).long() # since crossentropyloss takes an index (label) as argument
            move_pred, val_pred = model(in_tensor)
            move_pred = move_pred.masked_fill(~moves_mask.bool(), -1e9)


            sample_weights = sample_weights_func(depth)
            validation_loss += ((loss_policy(move_pred, move_tgt) + loss_val(val_pred, val_tgt)) * sample_weights).mean().item()
            correct += (move_pred.argmax(dim=1).long() == move_tgt).type(torch.float).sum().item()

    validation_loss /= num_batches
    correct /= size

    print(f"Validation Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss per batch: {validation_loss:>8f} \n")

    return validation_loss
            






if __name__ == "__main__":
    # print(model)
    # summary(model, input_size=(18, 8, 8))

    # in_tensor, move_tgt, val_tgt, depth = next(iter(train_dataloader))

    # out1, out2 = model(in_tensor)

    # print(out1)
    # print(out2)


    for t in range(EPOCHS):
        print(f"Epoch {t+1}\n-------------------------------")
        train_loop(train_dataloader, model, loss_policy, loss_val, optimizer) # train_dataloader instead of test_dataloader
        print("LR:", optimizer.param_groups[0]['lr'])
        val_loss = validation_loop(validation_dataloader, model, loss_policy, loss_val)
        scheduler.step(val_loss)
    print("Done!")

    torch.save(model.state_dict(), 'src/chess2/bot/saved_models/model_64_30_1e-3_1e-4_with_mask.pth')
