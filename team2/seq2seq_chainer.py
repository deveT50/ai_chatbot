#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#
#pip install mecab-python3
#python3 or 2 ??

import chainer
import chainer.functions as F
import chainer.links as L
from chainer import optimizers
import numpy as np
import sys
import codecs
import sqlite3
import MeCab

sys.stdout = codecs.getwriter('utf_8')(sys.stdout)

def to_words(sentence):
        """
        入力: 'すべて自分のほうへ'
        出力: tuple(['すべて', '自分', 'の', 'ほう', 'へ'])
        """
        tagger = MeCab.Tagger('mecabrc')  # 別のTaggerを使ってもいい
        mecab_result = tagger.parse(sentence)
        info_of_words = mecab_result.split('\n')
        words = []
        for info in info_of_words:
            # macabで分けると、文の最後に’’が、その手前に'EOS'が来る
            if info == 'EOS' or info == '':
                break
                # info => 'な\t助詞,終助詞,*,*,*,*,な,ナ,ナ'
            info_elems = info.split(',')
            # 6番目に、無活用系の単語が入る。もし6番目が'*'だったら0番目を入れる
            if info_elems[6] == '*':
                # info_elems[0] => 'ヴァンロッサム\t名詞'
                words.append(info_elems[0][:-3])
                continue
            words.append(info_elems[6])
        return tuple(words)

def make_input_output_vocab_dict():

    dbname = '../chat_data/conversation.db'
    input_vocab_list = ["<start>"]
    output_vocab_list = []

    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    conversation_pairs = conn.execute("select * from conversation_pair limit 10").fetchall()
    for convs in conversation_pairs:
        input_vocab_list.append(convs[2])
        output_vocab_list.append(convs[4])
        print "talk1: %s, talk2: %s" % (convs[2], convs[4])
    conn.close()

    input_vocab_list.append("<eos>")
    output_vocab_list.append("<eos>")
    return input_vocab_list, output_vocab_list

def make_vocab_dict(vocab):
    id2word = {}
    word2id = {}
    for id, word in enumerate(vocab):
        id2word[id] = word
        word2id[word] = id
    return id2word, word2id


class Seq2Seq(chainer.Chain):
    dropout_ratio = 0.5

    def __init__(self, input_vocab, output_vocab, feature_num, hidden_num):
        """
        :param input_vocab: array of input  vocab
        :param output_vocab: array of output  vocab
        :param feature_num: size of feature layer
        :param hidden_num: size of hidden layer
        :return:
        """
        self.id2word_input, self.word2id_input = make_vocab_dict(input_vocab)
        self.id2word_output, self.word2id_output = make_vocab_dict(output_vocab)
        self.input_vocab_size = len(self.word2id_input)
        self.output_vocab_size = len(self.word2id_output)

        super(Seq2Seq, self).__init__(
                # encoder
                word_vec=L.EmbedID(self.input_vocab_size, feature_num),
                input_vec=L.LSTM(feature_num, hidden_num),

                # connect layer
                context_lstm=L.LSTM(hidden_num, self.output_vocab_size),

                # decoder
                output_lstm=L.LSTM(self.output_vocab_size, self.output_vocab_size),
                out_word=L.Linear(self.output_vocab_size, self.output_vocab_size),
        )

    def encode(self, src_text, train):
        """
        :param src_text: input text embed id ex.) [ 1, 0 ,14 ,5 ]
        :param train : True or False
        :return: context vector
        """
        for word in src_text:
            word = chainer.Variable(np.array([[word]], dtype=np.int32))
            embed_vector = F.tanh(self.word_vec(word))
            input_feature = self.input_vec(embed_vector)
            context = self.context_lstm(F.dropout(input_feature, ratio=self.dropout_ratio, train=train))

        return context

    def decode(self, context, teacher_embed_id, train):
        """
        :param context: context vector which made `encode` function
        :param teacher_embed_id : embed id ( teacher's )
        :return: decoded embed vector
        """

        output_feature = self.output_lstm(context)
        predict_embed_id = self.out_word(output_feature)
        if train:
            t = np.array([teacher_embed_id], dtype=np.int32)
            t = chainer.Variable(t)
            return F.softmax_cross_entropy(predict_embed_id, t), predict_embed_id
        else:
            return predict_embed_id

    def initialize(self):
        """
        state initialize
        :param image_feature:
        :param train:
        :return:
        """
        self.input_vec.reset_state()
        self.context_lstm.reset_state()
        self.output_lstm.reset_state()

    def generate(self, start_word_id, sentence_limit):

        context = self.encode([start_word_id], train=False)
        sentence = ""

        for _ in range(sentence_limit):
            context = self.decode(context, teacher_embed_id=None, train=False)
            word = self.id2word_output[np.argmax(context.data)]
            if word == "<eos>":
                break
            sentence = sentence + word + " "
        return sentence


if __name__ == "__main__":

    tagger = MeCab.tagger('mecabrc')
    text = u'MeCabで遊んでみよう！'
    mecab_result = tagger.parse(text)
    print mecab_result

    # text = u'MeCabで遊んでみよう！'

    # print to_words(text.encode('utf-8'))
    # input_vocab_list, output_vocab_list = make_input_output_vocab_dict()


    # for input_vocab in input_vocab_list:
    #     print "11:", input_vocab
    #     # print to_words(input_vocab)

    ここでmecabのエラーが出てる！！！！

    # input_vocab = ["<start>"]
    # output_vocab = []

    # conn = sqlite3.connect(dbname)
    # c = conn.cursor()
    # conversation_pairs = conn.execute("select * from conversation_pair ").fetchall()
    # for convs in conversation_pairs:
    #     input_vocab.append(convs[2])
    #     output_vocab.append(convs[4])
    #     print "talk1: %s, talk2: %s" % (convs[2], convs[4])
    # conn.close()

    # input_vocab.append("<eos>")
    # output_vocab.append("<eos>")


    # input_vocab = ["<start>", u"黄昏に", u"天使の声", u"響く時，", u"聖なる泉の前にて", u"待つ", "<eos>"]
    # output_vocab = [u"5時に", u"噴水の前で", u"待ってます", "<eos>"]

    # model = Seq2Seq(input_vocab, output_vocab, feature_num=4, hidden_num=10)

    # optimizer = optimizers.SGD()
    # optimizer.setup(model)

    # for _ in range(20000):

    #     model.initialize()
    #     # reverse すると収束が早くなる
    #     input = [model.word2id_input[word] for word in reversed(input_vocab)]

    #     context = model.encode(input, train=True)
    #     acc_loss = 0

    #     for word in output_vocab:
    #         id = model.word2id_output[word]
    #         loss, context = model.decode(context, id, train=True)
    #         acc_loss += loss

    #     model.zerograds()
    #     acc_loss.backward()
    #     acc_loss.unchain_backward()
    #     optimizer.update()
    #     start = model.word2id_input["<start>"]
    #     sentence = model.generate(start, 7)

    #     print "teacher : ", "".join(input_vocab[1:6])
    #     print "-> ", sentence
    #     print



    # #modelとoptimizerを保存---------------------------------------------
    # print ('save the model')
    # serializers.save_npz('s2s.model', model)
    # print ('save the optimizer')
    # serializers.save_npz('s2s.state', optimizer)
