import mlflow
import os, sys
import json
import datetime
import time
import torch.nn as nn
import torch
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset
import numpy as np

import cv2 as cv
import pandas as pd
import math

from json_helper import log_print, read_json
from dataset import Template_Dataset


# ***Don't create instance of model directly, this is created in the trainer class
# The Model class inherits from the pytorch model class, and defines the layout of
# the neural network and the forward function of the network.
class __Model__(nn.Module):
    def __init__(self, dataset):
        super(__Model__, self).__init__()

        ### *** START MODEL SPECIFIC *** ###
        # Define the layout of your neural network layers here

        ### *** END MODEL SPECIFIC *** ###

    # the forward function, which is what transforms input data into output data at each layer of the
    # network
    def forward(self, index):

        ### *** START MODEL SPECIFIC *** ###
        # The forward function depends on the data being processed
        # and its layout.

        return index
        ### *** END MODEL SPECIFIC *** ###


# The Trainer class is used to define and train a pytorch model.
class Trainer:
    def __init__(self, training_params, logToMlFlow=True):
        self.training_params = training_params  # a dictionary of parameters from the JSON file for training
        self.run_name = None  # The run name gets set when the training is initialized (see logInitialize())
        self.logToMlFlow = logToMlFlow  # whether or not to log results to MLFlow

        self.dataset = Template_Dataset(
            self.training_params
        )  # the dataset to train the NN on
        self.createModel()

    # Create the pytorch model, which depends on the number of GPUs available for training
    def createModel(self):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # log the number of GPUs available
        log_print("Using", torch.cuda.device_count(), "GPUs!")

        # if multiple GPUs are available
        if torch.cuda.device_count() > 1:
            # use the DataParallel class
            self.model = nn.DataParallel(__Model__(self.dataset)).to(self.device)
            log_print("multiple gpus")
        else:
            # otherwise, just a basic model
            self.model = __Model__(self.dataset).to(self.device)
            log_print("single gpu")

    # Any code that needs to be run before the training begins goes here.
    # Right now it just sets up MLFlow to get it ready for logging.
    def initializeTraining(self):
        self.logInitialize()

    # The function that does the actual training.
    def train(self):
        ### *** START MODEL SPECIFIC *** ###
        # Define the criterion, optimizer, and dataLoader for the training
        criterion = torch.nn.MSELoss()
        optimizer = Adam(
            self.model.parameters(),
            lr=self.training_params.get("modelParams").get("lr"),
            betas=self.training_params.get("modelParams").get("betas"),
        )

        dataLoader = DataLoader(
            dataset=self.dataset,
            batch_size=self.training_params.get("modelParams").get("batch_size"),
            num_workers=2,
            pin_memory=True,
        )
        ### *** END MODEL SPECIFIC *** ###

        # get the number of epochs to run from the modelParams from the JSON file
        epochs = int(self.training_params.get("modelParams").get("epochs"))

        # call the trainEpoch function once for each epoch
        for epoch_index in range(epochs):
            try:
                self.trainEpoch(epoch_index, dataLoader, criterion, optimizer, epochs)

            except Exception as e:
                log_print(f"Exception {e}")

    # This function contains the code that should run every epoch. Also logs
    # the specified parameters to MLFlow.
    def trainEpoch(self, epoch_index, dataLoader, criterion, optimizer, epochs):

        # Start running of each epoch
        epoch_start = time.time()
        epoch_loss = 0.0

        ### *** START MODEL SPECIFIC *** ###
        # Write code that loops through the output
        # of your model, updating any values that you would like to output
        # to mlflow.

        ### *** END MODEL SPECIFIC *** ###

        epoch_end = time.time()

        ### *** START MODEL SPECIFIC *** ###
        # add metrics to log on every epoch here
        epochMetrics = {
            f"Epoch Training Time": epoch_end - epoch_start,
            f"Epoch Training Loss": epoch_loss,
        }
        ### *** END MODEL SPECIFIC *** ###

        self.logOnEpoch(epoch_index, epochMetrics)
        self.logOnEpochInterval(epoch_index, epoch_loss, epochs)

    # Any code that needs to be run after the training ends goes here.
    # Right now it just calls the function that ends the MLFlow logging.
    def endTraining(self):
        self.logEnd()

    ### START MLFLOW LOGGING METHODS ###

    # This function sets up MLFlow to get it ready for logging
    # parameters during training. It also sets the name of the run
    # to the branch name followed by the current date/time.
    def logInitialize(self):
        if self.logToMlFlow:
            branchName = str(self.training_params.get("gitParams").get("branchName"))
            dateTimeString = str(datetime.datetime.now().strftime("%m_%d_%y-%H_%M"))
            self.run_name = branchName + "-" + dateTimeString
            mlflow.set_tracking_uri("http://10.220.115.62:5000/")
            mlflow.start_run(run_name=self.run_name)
            mlflow.log_params(self.training_params)

    # This function logs each metric in a dictionary of metrics
    # to MLFlow, and is intended to be called every epoch.
    def logOnEpoch(self, epoch_index, metrics):
        if self.logToMlFlow:
            for key in metrics:
                mlflow.log_metric(key, metrics[key], epoch_index)

    # This function logs parameters on a specified epoch interval,
    # and saves the state of the system to a checkpoint file.
    def logOnEpochInterval(self, epoch_index, epoch_loss, epochs):
        if self.logToMlFlow:
            # get the epoch checkpoint logging interval from the JSON file
            log_interval = int(
                self.training_params.get("modelParams").get("logInterval")
            )

            # if this epoch is on the specified inteval, or it's the last epoch
            if (
                epoch_index % log_interval == 0 and epoch_index != 0
            ) or epoch_index == (epochs - 1):
                branchName = str(
                    self.training_params.get("gitParams").get("branchName")
                )

                # create a folder for the current branch
                checkpointPath = "ModelCheckpoints/" + branchName
                if not os.path.exists(checkpointPath):
                    os.makedirs(checkpointPath)

                # the filename is in the format "month_day_year-hour_minute"
                checkpoint_path = os.path.join(
                    checkpointPath,
                    datetime.datetime.now().strftime("%m_%d_%y-%H_%M") + ".pt",
                )

                ### *** START MODEL SPECIFIC *** ###
                # Any parameters to log to MLFlow on the specified epoch interval go here.
                # Right now, it just logs the path to the checkpoint.
                checkpointParams = {
                    f"Checkpoint Path for Epoch {epoch_index}": checkpoint_path
                }
                for key in checkpointParams:
                    mlflow.log_param(key, checkpointParams[key])
                ### *** END MODEL SPECIFIC *** ###

                # Save the model to the checkpoint
                state_dict = None

                if isinstance(self.model, nn.DataParallel):
                    state_dict = self.model.module.state_dict()
                else:
                    state_dict = self.model.state_dict()

                ### *** START MODEL SPECIFIC *** ###
                # Any parameters to save to the checkpoint go here
                torch.save(
                    {
                        "epoch": epoch_index,
                        "model_state_dict": state_dict,
                        "loss": epoch_loss,
                    },
                    checkpoint_path,
                )
                ### *** END MODEL SPECIFIC *** ###

    # This function ends the MLFlow run
    def logEnd(self):
        if self.logToMlFlow:
            mlflow.end_run()


if __name__ == "__main__":
    try:
        file = open("modelConfigTest.json")  # testing version
        # file = open(os.path.join(os.pardir, "modelConfig.json"))  # model version
        training_params = json.load(file)
        file.close()

        trainer = Trainer(training_params)
        trainer.initializeTraining()
        trainer.train()
        trainer.endTraining()

    except Exception as err:
        print(str(err.with_traceback()))
        f = open("error.txt", "w")
        f.write(str(err))
        f.close()
