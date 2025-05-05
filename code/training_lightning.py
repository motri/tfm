# -- Third-part modules -- #
import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
from datetime import datetime
import socket
import yaml
from sklearn.metrics import f1_score
import argparse
import mlflow
# --Proprietary modules -- #
from loadersLIGHT import (
    seed_everything,
    create_groupshuffle_split_fromcsv,
    build_dataset_train,
    build_dataset_test,
    create_dataloader_test
)  # Custom dataloaders for regular training and validation.

# from utils_models import create_table_metrics
from utils import Evaluator, create_table_metrics, f1_metric  # Functions to calculate metrics.
from unet import UNet  # Convolutional Neural Network model
from configurations import train_options  # Import training options.
import lightning as L  # Lightning module for training.
from torch.optim.lr_scheduler import ReduceLROnPlateau

class FocalLoss(nn.modules.loss._WeightedLoss):
    def __init__(self, weight=None, gamma=2,reduction='mean'):
        super(FocalLoss, self).__init__(weight,reduction=reduction)
        self.gamma = gamma
        self.weight = weight #weight parameter will act as the alpha parameter to balance class weights

    def forward(self, input, target):
        ce_loss = F.cross_entropy(input, target,reduction=self.reduction,weight=self.weight) 
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma * ce_loss).mean()
        return focal_loss


def create_data(config, debug=False):
    """
    Create the data loader for training and validation.
    """
    csvpath = config["csv_train_path"]
    min_perc_val = config["percentage_valid_pixels"]
    train_size = config["perc_training_scenes"]
    downsample_to_balance = config["downsample_to_balance"]
    batch_size = config["batch_size"]
    if "min_date" in config.keys():
        min_date = config["min_date"]
    else:
        min_date = None
    if "max_date" in config.keys():
        max_date = config["max_date"]
    else:
        max_date = None

    # -- Load the data -- #
    print("3. Load the data")
    complete_list_train_files, complete_list_val_files = next(
        create_groupshuffle_split_fromcsv(
            csvpath,
            min_perc_val,
            downsample_to_balance=downsample_to_balance,
            n_splits=1,
            train_size=train_size,
            random_state=0,
            logger=None,
            debug=False,
            min_date=min_date,
            max_date=max_date,
        )
    )
    print("3.1. DataLoader")
    dataloader = build_dataset_train(complete_list_train_files, config, batch_size)
    dataloader_val = build_dataset_test(complete_list_val_files, config, batch_size)
    print(
        f"\nREPORT:\npatches train: {len(dataloader.dataset)}\npatches validation: {len(dataloader_val.dataset)}\n"
    )
    print("Options initialised")
    return dataloader, dataloader_val


class bdSegmentor(L.LightningModule):
    """
    LightningModule for segmentation tasks, utilizing Clay Segmentor.

    Attributes:
        model (nn.Module): Clay Segmentor model.
        loss_fn (nn.Module): The loss function.
        iou (Metric): Intersection over Union metric.
        f1 (Metric): F1 Score metric.
        lr (float): Learning rate.
    """

    def __init__(
        self, config, f_loss, out_model_folder, csvpath=None, csvtestpath=None
    ):
        """
        Initialize the LightningModule.
        """
        super().__init__()
        self.save_hyperparameters()

        self.outfile_cm = out_model_folder / f"confusion_matrix.png"
        self.save_config_file = out_model_folder / "config.json"
        self.path_to_processed_data = Path(config["path_to_processed_data"])
        self.folder_npy = self.path_to_processed_data / "npy_patches"
        self.min_perc_val = config["percentage_valid_pixels"]
        self.train_size = config["perc_training_scenes"]
        self.downsample_to_balance = config["downsample_to_balance"]
        self.batch_size = config["batch_size"]
        self.config = config

        # Initialize evaluator for metrics such as accuracy, IoU, etc.
        self.evaluator = Evaluator(num_class=self.config["n_classes"]["SOD"])
        self.val_evaluator = Evaluator(num_class=self.config["n_classes"]["SOD"])
        # MANUAL
        self.table = create_table_metrics()
        self.table_val = create_table_metrics()
        # Setup U-Net model, adam optimizer, loss function and dataloader.
        self.net = UNet(options=config)
        self.loss_fn = f_loss
        self.weights = torch.FloatTensor(config["weight_loss"])
        if "pretrained_model_path" in config.keys():
            checkpoint = torch.load(config["pretrained_model_path"], weights_only=False)
            # change keys names , remove the first part of the key that has "net."
            checkpoint["state_dict"] = {
                key.replace("net.", ""): value for key, value in checkpoint["state_dict"].items()
            }
            checkpoint["state_dict"].pop('loss_fn.weight', None)
            self.net.load_state_dict(checkpoint["state_dict"])
            print(f"\nLOADED pretrained model stored in \n{config['pretrained_model_path']}\n")

        if self.outfile_cm.exists():
            print(f"\n\n\n\n{Path(out_model_folder).name} Already trained\n\n\n\n")
            self.already_trained = True
            return
        else:
            self.already_trained = False
            print(f"\n\n\n\n{Path(out_model_folder).name} Training\n\n\n\n")
        self.count_steps = 0
        self.loss_tot_train = []
        self.loss_tot_val = []
        self.tot_f1_absolute = []

    def configure_optimizers(self):
        """
        Configure the optimizer and learning rate scheduler.

        Returns:
            dict: A dictionary containing the optimizer and scheduler
            configuration.
        """
        optimizer = optim.AdamW(
            [
                param
                for name, param in self.net.named_parameters()
                if param.requires_grad
            ],
            lr=self.config["lr"],
            weight_decay=self.config["weight_decay"],
        )
        # scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
        #     optimizer,
        #     T_0=1000,
        #     T_mult=1,
        #     eta_min=self.config["lr"] * 100,
        #     last_epoch=-1,
        # )
        scheduler = {
            'scheduler': ReduceLROnPlateau(optimizer, mode='max', patience=10, factor=0.1),
            'monitor': 'val/f1_noweights_epoch',
            'interval': 'epoch',
            'frequency': 1
        }
        return {'optimizer': optimizer, 'lr_scheduler': scheduler}
        #     "optimizer": optimizer,
        #     # "lr_scheduler": {
        #     #     "scheduler": scheduler,
        #     #     "interval": "step",
        #     # },
        # }

    def log_metrics(self, phase, metrics_names, metrics_values, suffix = "", **kwargs):
        for elem, name in zip(metrics_values, metrics_names):
            if isinstance(elem, np.ndarray):
                # log every element of the array
                for idx, elem_ in enumerate(elem):
                    self.log(
                        f"{phase}/{name}_{idx}_{suffix}",
                        elem_,
                        **kwargs
                    )
                        # on_step=True,
                        # on_epoch=True,
                        # prog_bar=True,
                        # logger=True,
                        # sync_dist=True,
                    # )
            else:
                self.log(
                    f"{phase}/{name}_{suffix}",
                    elem,
                    **kwargs
                )
                    # on_step=True,
                    # on_epoch=True,
                    # prog_bar=True,
                    # logger=True,
                    # sync_dist=True,
                # )

    def calculate_metrics(self, class_evaluator, table_evaluator, inf_ys_flat=None, outputs_flat=None):
        
        if (inf_ys_flat is not None) & (outputs_flat is not None):  # update class_evaluator and table_evaluator
            class_evaluator.add_batch(inf_ys_flat, outputs_flat) 
            table_evaluator = create_table_metrics(
                table_evaluator, pred=inf_ys_flat, target=outputs_flat
            )

        f1_of_each_class, f1_auto = class_evaluator.mean_and_separate_F1_score()
        miou, sub_miou = class_evaluator.mean_and_separate_mIoU_score()

        # - f1 score
        f1_single_classes = (
            2
            * table_evaluator["True Positive"]
            / (
                2 * table_evaluator["True Positive"]
                + table_evaluator["False Positive"]
                + table_evaluator["False Negative"]
            )
        )
        # replace NaN with 0 for f1_single_classes
        # f1_single_classes = np.nan_to_num(f1_single_classes)
        maskf1manual = np.isnan(f1_single_classes)
        f1_manual = np.ma.average(np.ma.MaskedArray(f1_single_classes, mask = maskf1manual), weights=self.weights)
        maskf1auto = np.isnan(f1_of_each_class)
        f1_auto = np.ma.average(np.ma.MaskedArray(f1_of_each_class, mask = maskf1auto), weights=self.weights)
        f1_auto_unweighted = np.nanmean(f1_of_each_class)
        return f1_of_each_class, f1_auto, f1_manual, f1_auto_unweighted, miou, sub_miou, class_evaluator, table_evaluator

    def shared_step(self, data, batch_idx, phase):
        """
        Shared step for training and validation.
        """
        batch_x, batch_y, s_masks, fname = data
        batch_x = batch_x.squeeze(1)
        batch_y = batch_y.squeeze(1)
        s_masks = s_masks.squeeze(1)
        output = self.net(batch_x)["SOD"]
        if s_masks.sum()>0:            
            # Expand s_masks to match the shape of output
            s_masks_expanded = s_masks.unsqueeze(1).expand_as(output)
            # Mask the output tensor using s_masks
            masked_output = output.transpose(1, 0)[~s_masks_expanded.transpose(1, 0)]
            # Mask the target tensor using s_masks
            masked_target = batch_y[~s_masks]
            # print unique values of masked_output
            loss = self.loss_fn(masked_output.view(output.shape[1],-1).transpose(1, 0), masked_target.to(torch.long))
        else:
            loss = self.loss_fn(input=output, target=batch_y.to(torch.long))
        # else:
        # if phase == "test":
        #     # replace 255 with 0
        #     batch_y[batch_y == 255] = 0
        # METRICS
        # - Final output layer, and storing of non masked pixels.
        output = torch.argmax(output, dim=1).squeeze()
        # print(s_masks.squeeze(0).shape, output.shape)
        outputs_flat = output[~s_masks.squeeze(0)].cpu().numpy().astype(int)
        inf_ys_flat = batch_y[~s_masks].cpu().numpy().astype(int)
        f1_absolute = f1_metric(
            true=batch_y[~s_masks],
            pred=output[~s_masks.squeeze(0)],
            num_classes=self.config["n_classes"]["SOD"],
        )
        del output, batch_x, batch_y, s_masks  # Free memory.
        
        f1_of_each_class,  f1_auto, f1_manual, f1_auto_unweighted, miou, sub_miou, class_evaluator, table_evaluator = self.calculate_metrics( 
            self.val_evaluator if phase == "val" else self.evaluator, 
            self.table_val if phase == "val" else self.table,
            inf_ys_flat, outputs_flat,
        )
        if (phase == "val") | (phase == "test"):
            self.val_evaluator = class_evaluator
            self.table_val = table_evaluator
            self.loss_tot_val.append(loss.item())
        else:   
            self.evaluator = class_evaluator
            self.table = table_evaluator
            self.loss_tot_train.append(loss.item())

        names_outs = [
            "loss",
            "sub_f1",
            "f1_auto",
            "f1_manual",
            "f1_noweights",
            "f1_absolute",
            "mIoU",
            "sub_mIoU",
        ]
        elements_to_log = [loss, f1_of_each_class, f1_auto, f1_manual, f1_auto_unweighted, f1_absolute, miou, sub_miou]
        self.count_steps += 1
        self.log_metrics(
            phase, 
            names_outs, 
            elements_to_log, 
            suffix = "step",
            on_step=True, 
            on_epoch=False, 
            prog_bar=True, 
            logger=True, 
            sync_dist=True
            )
        if not torch.isnan(f1_absolute):
            self.tot_f1_absolute.append(float(f1_absolute))
        return loss

    def shared_epoch(self, phase):
        self.count_steps = 0
        f1_of_each_class, f1_auto, f1_manual, f1_auto_unweighted, miou, sub_miou, class_evaluator, table_evaluator = self.calculate_metrics( 
            self.val_evaluator if phase == "val" else self.evaluator, 
            self.table_val if phase == "val" else self.table,
            None, None,
        )
        if phase == "val":
            loss_tot = np.array(self.loss_tot_val).mean() 
            self.loss_tot_val = []
        else:
            loss_tot = np.array(self.loss_tot_train).mean() 
            self.loss_tot_train = []
        f1tot_absolute = np.nanmean(self.tot_f1_absolute)
        
        print(f"\n\nF1 -- {phase}---{self.tot_f1_absolute}\n {np.nanmean(self.tot_f1_absolute)}\n{f1tot_absolute}\n")

        names_outs = [
            "loss",
            "sub_f1",
            "f1_auto",
            "f1_manual",
            "f1_noweights",
            "f1_absolute",
            "mIoU",
            "sub_mIoU",
        ]
        elements_to_log = [loss_tot, f1_of_each_class, f1_auto, f1_manual, f1_auto_unweighted, f1tot_absolute, miou, sub_miou]
        self.log_metrics(
            phase, 
            names_outs, 
            elements_to_log,
            suffix = "epoch",
            on_step=False, 
            on_epoch=True, 
            prog_bar=True, 
            logger=True, 
            sync_dist=True
            )
        # reset the evaluator and the table
        self.tot_f1_absolute = []
        if phase == "val":
            self.val_evaluator.reset()
            self.table_val = create_table_metrics()
        else:
            self.evaluator.reset()
            self.table = create_table_metrics()
        return f1_auto

    def training_step(self, batch, batch_idx):
        """
        Training step for the model.

        Args:
            batch (dict): A dictionary containing the batch data.
            batch_idx (int): The index of the batch.

        Returns:
            torch.Tensor: The loss value.
        """
        # self.logger.experiment.autolog()
        return self.shared_step(batch, batch_idx, "train")

    def validation_step(self, batch, batch_idx):
        """
        Validation step for the model.

        Args:
            batch (dict): A dictionary containing the batch data.
            batch_idx (int): The index of the batch.

        Returns:
            torch.Tensor: The loss value.
        """
        return self.shared_step(batch, batch_idx, "val")

    def test_step(self, batch, batch_idx):
        """
        Test step for the model.

        Args:
            batch (dict): A dictionary containing the batch data.
            batch_idx (int): The index of the batch.

        Returns:
            torch.Tensor: The loss value.
        """
        return self.shared_step(batch, batch_idx, "test")

    def on_test_epoch_end(self):
        """
        Test epoch end for the model.
        """
        return self.shared_epoch("test")

    def on_validation_epoch_end(self):
        """
        Validation epoch end for the model.
        """
        self.shared_epoch("val")

    def on_train_epoch_end(self):
        """
        Train epoch end for the model.
        """
        self.shared_epoch("train")


def setup_folder(outfold=".", added_str=""):
    """
    Create a folder for the model output using the current timestamp.
    """
    TIME_FORMAT_STR: str = "%b_%d_%H_%M_%S"
    # -- Setup output folder -- #
    host_name = socket.gethostname()
    timestamp = datetime.now().strftime(TIME_FORMAT_STR)
    file_prefix = f"{host_name}_{timestamp}"
    out_model_folder = Path(outfold) / (file_prefix + added_str)
    ### search if the folder already exists, with another timestamp
    existing_fold = list(
        out_model_folder.parent.glob(out_model_folder.name.replace(file_prefix, "*"))
    )
    if len(list(existing_fold)) == 1:
        out_model_folder = existing_fold[0]
    ##########################################
    ### create the folder
    out_model_folder.mkdir(parents=True, exist_ok=True)
    print(f"\n\n\n0. SAVING INTO: {out_model_folder}\n\n\n")
    return out_model_folder


def logger(out_model_folder, model_name = "unet_basic", project_name ="FINAL_seaice"):
    """
    Function to call a Wand logger for logging metrics and model weights.
    """
    logger = L.pytorch.loggers.WandbLogger(
        # "NEW_sea-ice"
        entity="vicom", 
        project=project_name,#"NEWNEW_sea-ice", 
        name = model_name, 
        log_model=False
    )
    csvlogger = L.pytorch.loggers.CSVLogger(save_dir=out_model_folder, name="metrics")
    return [logger, csvlogger]


def callbacks(out_model_folder, model_name="Unet_basic"):
    """
    Function to call a ModelCheckpoint callback for saving model weights.
    """
    callbacks = [  # ModelCheckpoint callback
        L.pytorch.callbacks.ModelCheckpoint(
            dirpath=f"{out_model_folder}/checkpoints",
            auto_insert_metric_name=False,
            filename=f"{model_name}"+"_epoch-{epoch:02d}_valf1-{val/f1_auto_epoch:.3f}",
            monitor="val/f1_auto_epoch",
            mode="max",
            save_last=True,
            save_top_k=2,
            save_weights_only=True,
            verbose=True,
        ),
        # LearningRateMonitor callback
        L.pytorch.callbacks.LearningRateMonitor(logging_interval="step"),
        L.pytorch.callbacks.StochasticWeightAveraging(swa_lrs=1e-2),
        # L.pytorch.callbacks.EarlyStopping(
        #     monitor="val/subIoU_2",
        #     patience=25,
        #     mode="max",
        #     verbose=True,
        #     check_finite=True,
        #     stopping_threshold=0.99,
        # ),
    ]
    return callbacks


if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Train Default U-NET segmentor')

    # Mandatory arguments
    parser.add_argument('--config_file', type=str, help='train config file path', default="./conf_training.yaml")
    args = parser.parse_args()
    config_file = args.config_file

    # read yaml file
    # config_file = "./conf_training.yaml"
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
    conf_path  = config["paths"]
    conf_model = config["model"]
    conf_data  = config["data"]
    conf_train_options = config["train_options"]
    debug = config["debug"]

    conf_model["model_name"] = config_file.split(".")[0]
    conf_path["path_to_outfolder"] = conf_path["path_to_outfolder"] + "/" + conf_model["model_name"]

    out_model_folder = setup_folder(
        conf_path["path_to_outfolder"],
        added_str=conf_model["model_name"],
    )
    # -- Create the data loader -- #
    train_dataloader, val_dataloader = create_data({**conf_path, **conf_data, **conf_train_options}, debug=debug)
    # -- Create the loss function -- #
    if "weight_loss" in conf_model.keys():
        # f_loss = torch.nn.CrossEntropyLoss(weight = torch.FloatTensor(conf_model["weight_loss"]))
        f_loss = FocalLoss(weight = torch.FloatTensor(conf_model["weight_loss"]))
    else:
        # f_loss = torch.nn.CrossEntropy()
        f_loss = FocalLoss()
        conf_model["weight_loss"] = [1,1,1,1,1,1]
    # -- Create the LightningModule -- #
    model = bdSegmentor({**conf_path,**conf_model,**conf_data}, f_loss, out_model_folder)
    # # -- Create the trainer -- #
    trainer = L.Trainer(
        # deterministic=True,
        benchmark=True,
        fast_dev_run=debug,
        logger=logger(out_model_folder, model_name=conf_model["model_name"], project_name=conf_model["project_name"]),
        callbacks=callbacks(out_model_folder, model_name=conf_model["model_name"]),
        max_epochs=conf_data["epochs"],
        max_steps=-1,
        num_sanity_val_steps=0,
        # overfit_batches=1,
        # enable_progress_bar=False
    )
    test_dataloader = create_dataloader_test(
            csv_file = conf_path["csv_test_path"],
            options = {**conf_path, **conf_data},
            processed_data_path= conf_path["path_to_processed_data_test"],
            batch_size=conf_data["batch_size"]
        )
    trainer.fit(model, train_dataloader, val_dataloader) #val_dataloader)
    if not debug:
        trainer.test(
            model,
            # ckpt_path="/gpfs/VICOMTECH/proiektuak/DI13/DIVINE/other_data_sentinel1_gpaolini/DATA/new_models_out/all_elements/abacus-005_Mar_14_10_44_25UNet_alldata/checkpoints/UNet_alldata-segment_epoch-37_valmIoU-0.276.ckpt", 
            ckpt_path = "best", 
            dataloaders=test_dataloader
            )
