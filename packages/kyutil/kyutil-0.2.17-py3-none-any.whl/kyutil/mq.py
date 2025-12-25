# -*- coding: UTF-8 -*-
"""
@Project ：ctdy 
@File    ：mq.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2024/11/14 下午11:42 
@Desc    ：说明：
"""
import pika


def set_consumer(channel, queue_name, on_message_callback, auto_ack=True):
    channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=auto_ack)


def get_channel(host="localhost", port=5672, username="", password="", exchange="amq.topic", exchange_type="topic", durable=True):
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable)
    return channel
