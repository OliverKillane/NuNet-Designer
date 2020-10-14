import math
from random import randint


# All activation and loss functions required for the neurons, are held within a class as static methods.
# Activation Functions return a tuple of: value, derivative.
class ActivationFunctions:

    # binstep (binary step) is used for binary classifiers.
    @staticmethod
    def binstep(value, constant=0):
        if value > 0:
            return 1, 0
        else:
            return 0, 0

    # linear returns a linear multiple of the input provided.
    @staticmethod
    def linear(value, constant=0):
        return constant * value, constant

    # expolinearunit (exponential linear unit) activation function.
    @staticmethod
    def expolinearunit(value, constant=0):
        if value > 0:
            return value, 1
        else:
            return constant * (math.e ** value - 1), constant * math.e ** value

    # softplus activation function.
    @staticmethod
    def softplus(value, constant=0):
        return math.log1p(1 + math.e ** value), (1 + math.e ** -value) ** -1

    # rectlinearunit (recified linear unit) activation function.
    @staticmethod
    def rectlinearunit(value, constant=0):
        if value > 0:
            return value, 1
        else:
            return 0, 0

    # leakyReLU (leaky rectified linear unit) activation function.
    @staticmethod
    def leakyReLU(value, constant=0):
        if value > 0:
            return value, 1
        else:
            return constant * value, constant

    # sigmoid activation function.
    @staticmethod
    def sigmoid(value, constant=0):
        sigmoid = (1 + math.e ** -value) ** -1
        return sigmoid, sigmoid * (1 - sigmoid)

    # tanh activation function (using math module for faster processing).
    @staticmethod
    def tanh(value, constant=0):
        tanh = math.tanh(value)
        return tanh, 1 - tanh ** 2

    # none returns the value, it is used in inputs where an activation function is not required.
    @staticmethod
    def none(value, constant=0):
        return value, 1


# LossFunctions is used as a container for the loss functions that can be used by output neurons.
class LossFunctions:

    # meansquarederror (Mean Squared Error or L2 Loss) loss function.
    @staticmethod
    def meansquarederror(label, predicted, constant=0):
        return (predicted - label) ** 2, -2 * (predicted - label)

    # l1loss (absolute loss) loss function.
    @staticmethod
    def l1loss(label, predicted, constant=0):
        return abs(label - predicted), abs(label - predicted) / (label - predicted)

    # logloss (Log Loss) loss function, used for binary classifiers.
    @staticmethod
    def logloss(label, predicted, constant=0):
        if label == 1:
            return - math.log1p(predicted), -1 / math.log1p(predicted)
        elif label == 0:
            return - math.log1p(1 - predicted), -1 / (1 - predicted)

    # hingeloss (Hinge Loss) loss function.
    @staticmethod
    def hingeloss(label, predicted, constant=0):
        return max(0, 1 - label * predicted), max(0, -label)

    # huberloss (Huber Loss) loss function (excludes outliers).
    @staticmethod
    def huberloss(label, predicted, constant):
        if abs(label - predicted) <= constant:
            return 0.5 * (label - predicted) ** 2, predicted - label
        else:
            return constant * abs(label - predicted) - (constant ** 2) / 2, -constant

    # logcoshloss (Log-Cosh Loss) loss function.
    @staticmethod
    def logcoshloss(label, predicted, constant=0):
        return math.log1p(math.cosh(predicted - label)), math.tanh(predicted - label)


# The neuron class contains attributes of a neuron, and the methods required for forward and back propagation.
class Neuron:
    # NeuronID used to generate unique neuron identities for referencing.
    neuronID = 0

    def __init__(self, position, activationtype, activationconstant=0):

        # Setting up the unique identity of the neuron.
        self.__identity = Neuron.neuronID

        # Incrementing the neuronID so that the next neuron created as an ID one higher.
        Neuron.neuronID += 1

        # Storing the neuron position in the grid (for referencing the editor's design).
        self.__position = position

        # Setting up neuron activation attributes

        # Storing the type of function to use.
        self._activationType = activationtype

        # Storing the constant to use.
        self._activationConstant = activationconstant

        # Storing a reference to the activation function being used.
        self._activationFunction = self._setactivation(activationtype)

        # Storing neuron connections, differentiating between 'to' and 'from' to aid with forward/back propagation.
        self._toSynapses = list()
        self._fromSynapses = list()

        # Setting up neuron values:
        # inputValue holds the value input to the neuron
        self._inputValue = float()

        # activationValue holds the value output by the neuron.
        self._activationValue = float()

        # activationderivative holds the derivative of the neuron's output for use in backpropagation.
        self._activationDerivative = float()

        # Holds the derivative being sent back by the backpropagation algorithm.
        self._backpropDerivative = float()

    # Setactivation uses the string name of the activation function to get the actual static function reference so that it can be called.
    def _setactivation(self, activation):

        # Temporarily storing the function references in a dictionary for easy access.
        activations = {"TANH": ActivationFunctions.tanh,
                       "SIGMOID": ActivationFunctions.sigmoid,
                       "LEAKY ReLU": ActivationFunctions.leakyReLU,
                       "ReLU": ActivationFunctions.rectlinearunit,
                       "SOFTPLUS": ActivationFunctions.softplus,
                       "eLU": ActivationFunctions.expolinearunit,
                       "LINEAR": ActivationFunctions.linear,
                       "BINARY STEP": ActivationFunctions.binstep,
                       "NONE": ActivationFunctions.none
                       }

        # returning the function reference
        return activations[activation]

    # resetvalues sets the values dependent on forward and back propagation to zero, ready for the next training cycle.
    def resetvalues(self):
        self._inputValue = 0
        self._activationValue = 0
        self._activationDerivative = 0
        self._backpropDerivative = 0

    # addtosynapse is used in the setup of the neuron, and stores the object references of the connected synapses that the neuron feeds to.
    def addtosynapse(self, synapseobject):
        self._toSynapses.append(synapseobject)

    # addfromsynapse is used in the neuron's setup and stores object references of synapses that feed into the neuron.
    def addfromsynapse(self, synapseobject):
        self._fromSynapses.append(synapseobject)

    # giveinput adds an input to the neuron (used by synapses feeding forwards a value).
    def giveinput(self, value):
        self._inputValue += value

    # givederivative adds a given derivative to the neuron, and is used by backpropagating synapses.
    def givederivative(self, derivative):
        self._backpropDerivative += derivative

    # passforwards creates the activation value and derivative. Storing the latter and sending the former to all synapses the neuron feeds into.
    def passforwards(self):
        self._activationValue, self._activationDerivative = self._activationFunction(self._inputValue, self._activationConstant)

        # Iterating through each connected synapse in order to pass the value onwards.
        for synapse in self._toSynapses:
            synapse.passforwards(self._activationValue)

    # passbackwards backpropagates the derivative of the neuron, multiplied by the derivative passed to it.
    def passbackwards(self):

        # multiplying the activationderivative by the derivative passed to the neuron.
        self._backpropDerivative *= self._activationDerivative

        # Iterating through each synapse that feeds into the neuron in order to pass the derivative to each.
        for synapse in self._fromSynapses:
            synapse.passbackwards(self._backpropDerivative)

    # getidentiy returns the unique id of the neuron.
    def getidentity(self):
        return self.__identity

    # getposition returns the position the neuron had within the grid (used for referencing the design).
    def getposition(self):
        return tuple(self.__position)

    # getactivationtype returns the string name of the activation function used.
    def getactivationtype(self):
        return self._activationType

    # gettosynapses returns a list of the synapses that the neuron feeds values into.
    def gettosynapses(self):
        return self._toSynapses

    # getfromsynapse returns a list of all the synapses that the neuron is fed from.
    def getfromsynapses(self):
        return self._fromSynapses

    # getinputvalue returns the value input into the neuron.
    def getinputvalue(self):
        return self._inputValue

    # getactivationvalue returns the value output by the neuron.
    def getactivationvalue(self):
        return self._activationValue

    # getactivationderivative returns the derivative of the neuron, that is used for backpropagation.
    def getactivationderivative(self):
        return self._activationDerivative

    # getbackpropderivative returns the derivative of the neuron with regards to loss.
    def getbackpropderivative(self):
        return self._backpropDerivative

    # gettype returns the type of object (in this case 'Neuron').
    def gettype(self):
        return 'Neuron'


# Input is used to hold the attributes and methods for an input neuron.
class Input(Neuron):
    def __init__(self, name, position, activationtype, activationconstant=0):
        # Initialising the Neuron class to inherit it's attributes and methods.
        # Note: some attributes (such as fromSynapse) are not used due to the nature of Input Neurons.
        Neuron.__init__(self, position, activationtype, activationconstant)

        # Setup of input name (name associated with the feature that is input to the network):
        self._name = name

    # passbackwards is overridden from the Neuron class (as there are no synapses to pass back to).
    def passbackwards(self):
        self._backpropDerivative *= self._activationDerivative

    # getname returns the name attribute of the input, this is used for adding the features of the same name to it.
    def getname(self):
        return self._name

    # gettype is overridden from the Neuron class and returns the type of object, in this case 'Input'.
    def gettype(self):
        return "Input"


# Output contains all attributes and methods required by an output neuron.
class Output(Neuron):
    def __init__(self, name, position, activationtype, activationconstant=0):

        # Initialising the Neuron class to inherit it's attributes and methods.
        # Note: some attributes (such as toSynapse) are not used due to the nature of output neurons.
        Neuron.__init__(self, position, activationtype, activationconstant)

        # Setup of output name (name associated with the label that is predicted by the network).
        self._name = name

        # Holding of the label for a given training iteration
        self._labelValue = None

    # setlabel is used in training to set the label value associated with the neuron.
    def setlabel(self, label):
        self._labelValue = label

    # setactivation is overridden from the Neuron class, and is used to create the function reference required.
    def _setactivation(self, activation):
        losses = {"LOG-COSH": LossFunctions.logcoshloss,
                  "HUBER LOSS": LossFunctions.huberloss,
                  "HINGE LOSS": LossFunctions.hingeloss,
                  "LOG LOSS": LossFunctions.logloss,
                  "L1-LOSS": LossFunctions.l1loss,
                  "MSE": LossFunctions.meansquarederror
                  }

        return losses[activation]

    # passforwards is overridden from the Neuron class, it checks for a label value, if present it calculates the loss and loss derivative.
    def passforwards(self):

        # Checking a label value is present to calculate loss from.
        if not self._labelValue is None:
            # Calculating loss and loss derivative.
            self._activationValue, self._activationDerivative = self._activationFunction(self._inputValue, self._labelValue, self._activationConstant)

            # Setting up the derivative to be backpropagated.
            self._backpropDerivative = self._activationDerivative

    # passbackwards is overridden from the Neuron class and sends the derivative of the neuron to each synapse feeding into it.
    def passbackwards(self):
        for synapse in self._fromSynapses:
            synapse.passbackwards(self._backpropDerivative)

    # getname returns the name of the output neuron (name of the label associated with that neuron).
    def getname(self):
        return self._name

    # getloss returns the loss of the output.
    def getloss(self):
        return self._activationValue

    # gettype is overridden from the Neuron class, it returns the type of object, in this case 'Output'.
    def gettype(self):
        return 'Output'


# The synapse class contains all attributes required for synapse connections (weight, bias, initialisations), and provides back and forward propagation
# functionality, it also adjusts its own weight and bias in accordance with the backpropagated derivative passed to it.
class Synapse:
    synapseID = 0

    def __init__(self, startposition, endposition, weightinitialisation, biasenabled):
        # setup of synapse identity
        self.__identity = Synapse.synapseID
        Synapse.synapseID += 1

        # Setup of initial positions
        self.__startPosition = startposition
        self.__endPosition = endposition

        # attribute to hold weight intitialisation parameters (interval, min, max)
        self.__weightInitialisation = weightinitialisation

        # Holder for neuron objects:
        self.__startNeuron = None
        self.__endNeuron = None

        # storing bias flag, if true a bias value is also created
        self.__biasEnabled = biasenabled

        # bias set to zero for start, hence if not enabled, will stay zero and not participate in any calculations for the synapse output
        self.__biasValue = float()

        # Storing the current weights of the synapse.
        self.__weightValue = float()

        # storing the input value to the synapse, this is used in changing synapse bias based on backpropagated derivative.
        self.__inputValue = float()

        # Storing the activation value of the synapse (the value it feeds forward).
        self.__activationValue = float()

        # Storing the backpropagated derivative of the synapse.
        self.__backpropDerivative = float()

        # Storing the learning rate (used to change the sensitivity of synapse weight and bias adjustment to backpropagated derivative.
        self.__learningRate = float()

        # Setting up the intial reandom weight and bias of the synapse.
        self.initialise()

    # initialise uses the passed weight initialisation settings to randomly generate the weight, bias.
    def initialise(self):
        range = self.__weightInitialisation["max"] - self.__weightInitialisation["min"]
        interval = self.__weightInitialisation["interval"]

        self.__weightValue = self.__weightInitialisation["min"] + randint(0, range // interval) * interval

        if self.__biasEnabled:
            self.__biasValue = self.__weightInitialisation["min"] + randint(0, range // interval) * interval

    # Resetvalues resets the values associated with the synapse for one training cycle.
    def resetvalues(self):

        # input, output and derivatives reset to zero.
        self.__inputValue = 0
        self.__activationValue = 0
        self.__backpropDerivative = 0

    # setlearningrate is used to set the learning rate of the synapse based on that of the network.
    def setlearningrate(self, learningrate):
        self.__learningRate = learningrate

    # passforwards passed the activation of the synapse onto the neuron, or output it feeds into.
    def passforwards(self, value):

        # storing the new input value
        self.__inputValue = value

        # calculating the activation, if w is weight, x input and bias: activation = wx + b.
        self.__activationValue = self.__inputValue * self.__weightValue + self.__biasValue

        # Feeding the result to the next neuron or input.
        self.__endNeuron.giveinput(self.__activationValue)

    # passbackwards adjusts the neuron weight (and bias if applicable) and passed the derivative onto the input or neuron before it.
    def passbackwards(self, derivative):

        # Adjusting synapse bias.
        if self.__biasEnabled:
            self.__biasValue -= derivative * self.__learningRate

        # Backpropagating the derivative of the input to the synapse, with regard to loss.
        self.__backpropDerivative = derivative * self.__weightValue
        self.__startNeuron.givederivative(self.__backpropDerivative)

        # Adjusting the weight.
        self.__weightValue -= self.__inputValue * derivative * self.__learningRate

    # setneurons is used in the setup of the synapse, and provides it with the objects of the two neuron type objects it connects to.
    def setneurons(self, start, end):
        self.__startNeuron = start
        self.__endNeuron = end

    # getidentity returns the unique identity of the synapse
    def getidentity(self):
        return self.__identity

    # getstartposition returns the start-position of the synapse in the design grid.
    def getstartposition(self):
        return tuple(self.__startPosition)

    # getendposition returns the end-position of the synapse in the design grid.
    def getendposition(self):
        return tuple(self.__endPosition)

    # getstartneuron returns the neuron the synapse feeds from.
    def getstartneuron(self):
        return self.__startNeuron

    # getendneuron returns the neuron the synapse feeds into.
    def getendneuron(self):
        return self.__endNeuron

    # getbiasenabled returns True if the bias option is enabled for the neuron.
    def getbiasenabled(self):
        return self.__biasEnabled

    # getbiasvalue returns the value of the bias.
    def getbiasvalue(self):
        if self.__biasEnabled:
            return self.__biasValue
        else:
            return None

    # getweightvalue returns the weight of the synapse.
    def getweightvalue(self):
        return self.__weightValue

    # getinputvalue returns the value of the input last given to the synapse in the current training cycle.
    def getinputvalue(self):
        return self.__inputValue

    # getactivationvalue returns the last activation/output of the synapse in the current training cycle.
    def getactivationvalue(self):
        return self.__activationValue

    # getbackpropderivative returns the derivative of the synapse input with regard to the loss.
    def getbackpropderivative(self):
        return self.__backpropDerivative

    # gettype returns the type of object, in this case 'synapse'.
    def gettype(self):
        return 'Synapse'


# The network class stores the structure of the network, and manages the forward and backpropagation algorithms.
class Network:
    def __init__(self, neurons, synapses, learningrate):

        # Storing the neuron objects as a 2D array, with each index being a list of a given layer's neurons.
        self._neurons = neurons

        # Storing a list of all synapse objects in the network.
        self._synapses = synapses

        # Setting up a dictionary with items {feature name : corresponding input neuron}, to more easily set inputs.
        self._inputs = dict()

        # Setting up a dictionary with items {label name : corresponding output neuron}, to more easily set inputs.
        self._outputs = dict()

        # Storing the network's learning rate.
        self._learningRate = learningrate

        # usng a temporary dictionary to holds neurons with their position as the key (used for connecting synapse and neuron objects).
        neurondict = dict()
        for layer in neurons:
            for neuronobject in layer:
                neurondict[neuronobject.getposition()] = neuronobject

        # Iterating through each synapses, adding a reference to it in the neurons it connects, and a reference to the neurons it connects to it.
        for synapseobject in self._synapses:
            # Finding the start and end neurons.
            startneuron = neurondict[synapseobject.getstartposition()]
            endneuron = neurondict[synapseobject.getendposition()]

            # Adding the start and end neurons to the synapse object.
            synapseobject.setneurons(startneuron, endneuron)

            # Adding the synapse to the start and end neurons.
            startneuron.addtosynapse(synapseobject)
            endneuron.addfromsynapse(synapseobject)

        # Iterating through the layers, then neurons, in order to add input neurons to 'inputs' and output neurons to 'outputs'.
        for layer in self._neurons:
            for neuronobject in layer:
                if neuronobject.gettype() == "Input":
                    self._inputs[neuronobject.getname()] = neuronobject
                elif neuronobject.gettype() == "Output":
                    self._outputs[neuronobject.getname()] = neuronobject

        # initialising random values for weight (and bias if required) of the synapses.
        self.initialise()

    # initialise is used set weight and bias values for synapses to random (based on their initialisation settings - Min, Max, Interval).
    def initialise(self):

        # Setting up learning rates for synapses.
        self.setlearningrate(self._learningRate)

        # Iterating through all synapses in the network.
        for synapse in self._synapses:
            # Running a given synapse's initialise method.
            synapse.initialise()

    # resetvalues is used to set all training cycle dependent attributes of neurons and synapses to zero (their current value, derivative)
    def _resetvalues(self):

        # Iterating through each layer in the network.
        for layer in self._neurons:

            # Iterating through each neuron in the layer.
            for neuronobject in layer:
                # Resetting the neuron's values.
                neuronobject.resetvalues()

        # Iterating through each synapse in the network.
        for synapseobject in self._synapses:
            # Resetting the synapse's values.
            synapseobject.resetvalues()

    # feedforward forward propagates a given set of features through the network.
    def _feedforward(self, features):

        # Resetting synapse and neuron values for the next pass.
        self._resetvalues()

        # adding each feature to its corresponding input neuron.
        for featurekey in features.keys():
            self._inputs[featurekey].giveinput(features[featurekey])

        # Instructing each neuron in each layer (in order) to pass their value forwards.
        for layer in self._neurons:
            for neuronobject in layer:
                neuronobject.passforwards()

    # Setlabels is used to provide the output neurons their corresponding labels for a given training cycle.
    def _setlabels(self, labels):
        for labelkey in labels.keys():
            self._outputs[labelkey].setlabel(labels[labelkey])

    # backpropagate instructs each neuron to send its derivative multiplied by the derivative passed to it, to its synapses, which adjust and then their derivative
    # to their start neurons.
    def _backpropagate(self):

        # Iterating backwards through the layers.
        for layer in self._neurons[::-1]:
            for neuronobject in layer:
                neuronobject.passbackwards()

    # setlearningrate sets the learning rate of every synapse to that of the network.
    def setlearningrate(self, learningrate):
        self._learningRate = learningrate
        for synapse in self._synapses:
            synapse.setlearningrate(learningrate)

    # predict is used to retreive the prediction made by the network from a given set of features.
    def predict(self, features):
        self._feedforward(features)
        return {output.getname(): output.getinputvalue() for output in self._outputs.values()}

    # test is used to generate statistics about the current loss of the network over a given test dataset, without changing the network's weights and biases.
    def test(self, featurelist, labellist):

        # Setting up a list for inputs, outputs and the loss for the different labels.
        testcycles = list()

        # Setting up a dictionary to hold the average label loss over the training dataset.
        averagelabelloss = {labelname : 0 for labelname in labellist[0].keys()}

        # Iterating through the passed dataset.
        for cycle in range(0, len(featurelist)):

            # Setting the label values for the output neurons.
            self._setlabels(labellist[cycle])

            # Forward propagating to the output neurons (this calculates the loss).
            self._feedforward(featurelist[cycle])

            # Stroing the loss for the given set of labels.
            loss = {output.getname(): output.getloss() for output in self._outputs.values()}

            # Appending the features, labels and loss to the list for each prediction cycle.
            testcycles.append({"features": featurelist[cycle], "labels": labellist[cycle], "loss": loss})

            # Adding the loss in each output to its respective part of the loss doctionary
            for labelname in loss.keys():
                averagelabelloss[labelname] += loss[labelname]

        # Dividing the loss of each sum of loss in the loss dictionary by the number of cycles to calculate mean loss.
        cycles = len(featurelist)
        for labelname in averagelabelloss:
            averagelabelloss[labelname] /= cycles

        # Returning a list of the test cycles, and the mean loss.
        return testcycles, averagelabelloss

    # train is used to repeatedly forward propagate, then backpropagate and adjust the network to allow it to learn for a set of data.
    def train(self, featurelist, labellist, cycles, record=True, display=True):

        # Creating a list to store the values for each training cycle.
        trainingrecord = list()

        # Iterating through the number of cycles required.
        for cycle in range(0, cycles):

            # Storing the index of the feature to be input (as cycles can be longer than the feature list if the user wants data to be used multiple times).
            dataindex = cycle % len(featurelist)

            # Setting the labels of the output neurons.
            self._setlabels(labellist[dataindex])

            # Feeding forward the inputs.
            self._feedforward(featurelist[dataindex])

            # Backpropagating the loss derivative, and adjusting synapse weights and biases in the process.
            self._backpropagate()

            # If the user has opted to display, the network state is displayed, with current values included.
            if display:
                print("\n\nCycle:   " + str(cycle))
                self.displaynetwork(True)

            # If the user has opted to record the training cycles, the cycle data is added to the training record.
            if record:
                trainingrecord.append(
                    {"cycle": cycle, "features": featurelist[dataindex], "labels": labellist[dataindex], "predicted": {output.getname(): output.getinputvalue() for output in self._outputs.values()},
                     "loss": {output.getname(): output.getloss() for output in self._outputs.values()}})

        # If the user opts to receive training data, it is returned.
        if record:
            return trainingrecord

    # displaynetwork displays the network's neurons and synapse attributes. If value is True (False by default), cycle associated values are also displayed.
    def displaynetwork(self, values=False):

        # Displaying the title for the user.
        print("\n" + "*" * 30 + "NETWORK VALUES" + "*" * 30)

        # Displaying all neuron values.
        print("Neurons:")

        # Iterating through each layer.
        for layer in range(0, len(self._neurons)):
            print("\tLayer: " + str(layer))

            # Iterating through each neuron in each layer.
            for neuron in self._neurons[layer]:

                # Printing key attributes.
                print("\t\tNeuron ID: " + str(neuron.getidentity()))
                print("\t\t\tType:\t\t\t" + neuron.gettype())
                print("\t\t\tActivation:\t" + neuron.getactivationtype())

                # If values is True, input, activation value and backpropagated derivative are printed.
                if values:
                    print("\t\t\tInput:\t\t\t" + str(neuron.getinputvalue()))
                    print("\t\t\tA-Value:\t\t" + str(neuron.getactivationvalue()))
                    print("\t\t\tDerivative:\t" + str(neuron.getbackpropderivative()))
                print()

        # Displaying all synapse attributes.
        print("\nSynapses:")

        # Iterating through each synapse in the network.
        for synapse in self._synapses:

            # Printing key attributes.
            print("\tSynapse ID: " + str(synapse.getidentity()))
            print("\t\tStart Neuron:\t" + str(synapse.getstartneuron().getidentity()))
            print("\t\tEnd Neuron:\t\t" + str(synapse.getendneuron().getidentity()))
            print("\t\tWeight:\t\t\t" + str(synapse.getweightvalue()))

            # IF there is a bias, bias is printed, else 'Bias Not Enabled'
            if synapse.getbiasenabled():
                print("\t\tBias:\t\t\t" + str(synapse.getbiasvalue()))
            else:
                print("\t\tBias:\t\t\tBias Not Enabled")

            # If values is true, cycle dependent values for the synapse are printed.
            if values:
                print("\t\tInput:\t\t\t" + str(synapse.getinputvalue()))
                print("\t\tValue:\t\t\t" + str(synapse.getactivationvalue()))
                print("\t\tDerivative:\t\t" + str(synapse.getbackpropderivative()))
            print()

        # Printing the end of the data.
        print("*" * 74)

    # getlearningrate returns the learning rate of the network.
    def getlearningrate(self):
        return self._learningRate

    # getsynapse uses the synapse identity to return a given synapse object.
    def getsynapse(self, identity):

        # Iterating through all synapses.
        for synapse in self._synapses:

            # If synapse identity matchs identity being searched for, return the synapse.
            if synapse.getidentity() == identity:
                return synapse

        # If identity is not present for a synapse in the network, return None
        return None

    # getneuron returns a neuron object for a given identity.
    def getneuron(self, identity):

        # Iterating through each layer.
        for layer in self._neurons:

            # Iterating through each neuron in the layer.
            for neuron in layer:

                # If the neuron identity matches, return the neuron.
                if neuron.getidentity() == identity:
                    return neuron

        # If there are no neurons with the provided identity, return None.
        return None