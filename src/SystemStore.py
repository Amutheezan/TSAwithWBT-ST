import operator
import os
import shutil
from sklearn.externals import joblib

# SELF_TRAINING PARAMETERS

# {'kernel': 'rbf', 'C' : 0.28, 'gamma' :1.0} 0.65

# CO_TRAINING PARAMETERS

#  Feature Set 1
#  {'kernel': 'rbf', 'C': 0.7, 'gamma': 1.0} 0.591580193034
#  {'kernel': 'rbf', 'C': 0.73, 'gamma': 1.02} 0.593126981136

# Feature Set 0
# {'kernel': 'rbf', 'C': 0.1, 'gamma': 0.1} 0.0628731514651
# {'kernel': 'rbf', 'C': 0.1, 'gamma': 0.1} 0.0628731514651


class Constants:
    # Location of files to be loaded
    FILE_LABELED = "../dataset/semeval2014.csv"
    FILE_UN_LABELED = "../dataset/unlabeled.csv"
    FILE_TEST = "../dataset/test2014.csv"
    FILE_TUNE = "../dataset/tune2014.csv"

    # Constant relevant to Classifier [SVM]
    CLASSIFIER_SVM = "svm"
    KERNEL_LINEAR = "linear"
    KERNEL_RBF = "rbf"

    # Test type of SemEval 2013/2014
    TEST_TYPE_TWITTER_2013 = "Twitter2013"
    TEST_TYPE_TWITTER_2014 = "Twitter2014"
    TEST_TYPE_TWITTER_SARCASM = "Twitter2014Sarcasm"

    NO_TOPIC = "###NO###TOPIC###"
    NO_OF_TOPICS = 10

    # Label float values
    LABEL_POSITIVE = 2.0
    LABEL_NEGATIVE = -2.0
    LABEL_NEUTRAL = 0.0
    UNLABELED = -4.0

    # Label String Values
    NAME_POSITIVE = "positive"
    NAME_NEGATIVE = "negative"
    NAME_NEUTRAL = "neutral"

    # Training Set Ratio
    POS_RATIO = 0.3734
    NEG_RATIO = 0.1511
    NEU_RATIO = 0.4754

    # Full Data set size
    LABEL_DATA_SET_SIZE = 9684
    TEST_DATA_SET_SIZE = 8987

    # training type
    SELF_TRAINING_TYPE = "st"
    CO_TRAINING_TYPE = "ct"
    TOPIC_BASED_TRAINING_TYPE = "tb"

    # Constants relevant at predicting
    PERCENTAGE_MINIMUM_DIFF = 0.1
    PERCENTAGE_MINIMUM_CONF_CO = 0.9
    PERCENTAGE_MINIMUM_CONF_SELF = 0.5

    CSV_HEADER = [ "TEST_TYPE" , "POS" , "NEG" , "NEU" , "ITER" , "ACCURACY" ,
                   "PRE-POS" , "PRE-NEG" , "RE-POS" , "RE-NEG" ,
                   "F1-POS" , "F1-NEG" , "F1-AVG" ]

    def __init__(self):
        self.DEFAULT_CLASSIFIER = self.CLASSIFIER_SVM
        self._setup_()

    def _setup_(self):
        self.TEST_TYPES = [self.TEST_TYPE_TWITTER_2013,
                           self.TEST_TYPE_TWITTER_2014,self.TEST_TYPE_TWITTER_SARCASM]

        self.LABEL_TYPES = [self.LABEL_POSITIVE, self.LABEL_NEGATIVE,self.LABEL_NEUTRAL]

        if self.DEFAULT_CLASSIFIER == self.CLASSIFIER_SVM:
            self.DEFAULT_KERNEL_0 = self.KERNEL_RBF
            self.DEFAULT_C_PARAMETER_0 = 0.1
            self.DEFAULT_GAMMA_SVM_0 = 0.1
            self.DEFAULT_KERNEL = self.KERNEL_RBF
            self.DEFAULT_C_PARAMETER = 0.73
            self.DEFAULT_GAMMA_SVM = 1.02
            self.DEFAULT_KERNEL_SELF = self.KERNEL_RBF
            self.DEFAULT_C_PARAMETER_SELF = 0.28
            self.DEFAULT_GAMMA_SVM_SELF = 1.00


class Commons:

    def __init__(self, cons):
        self.cons = cons

    def temp_difference_cal(self,time_list):
        if len(time_list) > 1:
            final = float(time_list[len(time_list) - 1])
            initial = float(time_list[len(time_list) - 2])
            difference = final - initial
        else:
            difference = -1.0
        return difference

    def dict_update(self,original, temp):
        result = {}
        original_temp = original.copy()
        for key in temp.keys():
            global_key_value = original_temp.get(key)
            local_key_value = temp.get(key)
            if key not in original_temp.keys():
                result.update({key: local_key_value})
            else:
                result.update({key: local_key_value + global_key_value})
                del original_temp[key]
        result.update(original_temp)
        return result

    def get_divided_value(self,numerator, denominator):
        if denominator == 0:
            return 0.0
        else:
            result = numerator / (denominator * 1.0)
            return round(result, 4)

    def first_next_max(self,input_list):
        first = 0.0
        next = 0.0
        for element in input_list:
            if element > first:
                next = first
                first = element
            elif element > next:
                next = element
        return first , next

    def find_max_value_in_dict(self , dictionary):
        maximum = max(dictionary.iteritems() , key=operator.itemgetter(1))[ 1 ]
        key = max(dictionary.iteritems() , key=operator.itemgetter(1))[ 0 ]
        return maximum , key

    def get_labels(self , p , prob):
        l = self.cons.UNLABELED
        if prob[ 0 ] == p:
            l = self.cons.LABEL_NEGATIVE
        if prob[ 1 ] == p:
            l = self.cons.LABEL_NEUTRAL
        if prob[ 2 ] == p:
            l = self.cons.LABEL_POSITIVE
        return l

    def get_sum_proba(self,first , second):
        result = [ ]
        for i in range(len(first)):
            result.append(0.5 * (first[ i ] + second[ i ]))
        return result

    def get_values(self,actual, predict):
        TP = 0
        TN = 0
        TNeu = 0
        FP_N = 0
        FP_Neu = 0
        FN_P = 0
        FN_Neu = 0
        FNeu_P = 0
        FNeu_N = 0
        for i in range(len(actual)):
            a = actual[i]
            p = predict[i]
            if a == p:
                if a == self.cons.LABEL_POSITIVE:
                    TP += 1
                if a == self.cons.LABEL_NEUTRAL:
                    TNeu += 1
                if a == self.cons.LABEL_NEGATIVE:
                    TN += 1
            if a != p:
                if a == self.cons.LABEL_POSITIVE:
                    if p == self.cons.LABEL_NEGATIVE:
                        FN_P +=1
                    if p == self.cons.LABEL_NEUTRAL:
                        FNeu_P +=1
                if a == self.cons.LABEL_NEGATIVE:
                    if p == self.cons.LABEL_POSITIVE:
                        FP_N += 1
                    if p == self.cons.LABEL_NEUTRAL:
                        FNeu_N += 1
                if a == self.cons.LABEL_NEUTRAL:
                    if p == self.cons.LABEL_POSITIVE:
                        FP_Neu += 1
                    if p == self.cons.LABEL_NEGATIVE:
                        FN_Neu += 1

        accuracy = self.get_divided_value(TP+TN+TNeu, TP+TN+TNeu+FP_N+FP_Neu+FN_P+FN_Neu+FNeu_P+FNeu_N)
        pre_pos = self.get_divided_value(TP , TP + FP_Neu + FP_N)
        pre_neg = self.get_divided_value(TN , TN + FN_Neu + FN_P)
        re_pos = self.get_divided_value(TP,TP+FNeu_P+FN_P)
        re_neg = self.get_divided_value(TN,TN+FNeu_N+FP_N)
        f1_pos = 2 * self.get_divided_value(pre_pos * re_pos , pre_pos + re_pos)
        f1_neg = 2 * self.get_divided_value(pre_neg * re_neg , pre_neg + re_neg)
        return accuracy,pre_pos,pre_neg,re_pos,re_neg,f1_pos,f1_neg, 0.5 * (f1_neg + f1_pos)


class DataStore:
    ANALYSED_DIRECTORY = "../dataset/analysed/"
    TEMP_DIRECTORY = "../dataset/temp/"
    VECTOR_TEMP_STORE = TEMP_DIRECTORY + "vector/"
    LABEL_TEMP_STORE = TEMP_DIRECTORY + "label/"
    MODEL_TEMP_STORE = TEMP_DIRECTORY + "model/"
    SCALAR_TEMP_STORE = TEMP_DIRECTORY + "scalar/"
    NORMALIZER_TEMP_STORE = TEMP_DIRECTORY + "normalizer/"

    def __init__(self, cons):
        self.cons = cons
        self.TRAIN_DICT = {}
        self.TOPICS = {}

        self.POS_INITIAL = 0
        self.NEG_INITIAL = 0
        self.NEU_INITIAL = 0

        self.POS_SIZE = 0
        self.NEG_SIZE = 0
        self.NEU_SIZE = 0

        self.POS_UNI_GRAM = {}
        self.NEG_UNI_GRAM = {}
        self.NEU_UNI_GRAM = {}

        self.POS_POST_UNI_GRAM = {}
        self.NEG_POST_UNI_GRAM = {}
        self.NEU_POST_UNI_GRAM = {}

        self.CURRENT_ITERATION = 0

        self.SUB_DIRECTORY = [self.VECTOR_TEMP_STORE,self.LABEL_TEMP_STORE,self.MODEL_TEMP_STORE,self.SCALAR_TEMP_STORE,self.NORMALIZER_TEMP_STORE]
        self._create_directories_()

    def _create_directories_(self):
        self._create_directory_(self.ANALYSED_DIRECTORY)
        self._delete_directory_(self.TEMP_DIRECTORY)
        self._create_directory_(self.TEMP_DIRECTORY)
        for directory in self.SUB_DIRECTORY:
            self._create_directory_(directory)

    def _create_mode_iteration_directories(self, mode, topic):
        for directory in self.SUB_DIRECTORY:
            topic_directory = directory + "/" + str(topic)
            mode_directory = topic_directory + "/" + str(mode)
            iteration_directory = mode_directory + "/" + str(self._get_current_iteration_())
            self._create_directory_(topic_directory)
            self._create_directory_(mode_directory)
            self._create_directory_(iteration_directory)

    def _dump_vectors_labels_(self , vectors , labels , mode):
        self._create_mode_iteration_directories(mode, self.cons.NO_TOPIC)
        joblib.dump(vectors, self.VECTOR_TEMP_STORE + self._get_suffix_(mode, self.cons.NO_TOPIC))
        joblib.dump(labels, self.LABEL_TEMP_STORE + self._get_suffix_(mode, self.cons.NO_TOPIC))

    def _dump_model_scaler_normalizer_(self , model , scalar , normalizer , mode , topic):
        self._create_mode_iteration_directories(mode, topic)
        joblib.dump(model , self.MODEL_TEMP_STORE + self._get_suffix_(mode, topic))
        joblib.dump(scalar , self.SCALAR_TEMP_STORE + self._get_suffix_(mode, topic))
        joblib.dump(normalizer , self.NORMALIZER_TEMP_STORE + self._get_suffix_(mode,topic))

    def _get_vectors_(self, mode):
        return joblib.load(self.VECTOR_TEMP_STORE + self._get_suffix_(mode,self.cons.NO_TOPIC))

    def _get_labels_(self, mode):
        return joblib.load(self.LABEL_TEMP_STORE + self._get_suffix_(mode,self.cons.NO_TOPIC))

    def _get_scalar_(self, mode,topic):
        return joblib.load(self.SCALAR_TEMP_STORE + self._get_suffix_(mode,topic))

    def _get_normalizer_(self, mode, topic):
        return joblib.load(self.NORMALIZER_TEMP_STORE + self._get_suffix_(mode,topic))

    def _get_model_(self , mode , topic):
        return joblib.load(self.MODEL_TEMP_STORE + self._get_suffix_(mode,topic))

    def _get_suffix_(self, mode, topic):
        suffix = str(topic) + "/" + str(mode) + "/" + str(self._get_current_iteration_()) +"/store.plk"
        return suffix

    def _create_directory_(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _delete_directory_(self,directory):
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def _increment_iteration_(self):
        self.CURRENT_ITERATION += 1

    def _get_current_iteration_(self):
        return self.CURRENT_ITERATION

    def _update_uni_gram_(self , pos , neg , neu , is_pos_tag):
            if is_pos_tag:
                self.POS_POST_UNI_GRAM = pos
                self.NEG_POST_UNI_GRAM = neg
                self.NEU_POST_UNI_GRAM = neu
            if not is_pos_tag:
                self.POS_UNI_GRAM = pos
                self.NEG_UNI_GRAM = neg
                self.NEU_UNI_GRAM = neu