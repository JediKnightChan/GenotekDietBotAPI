from __future__ import absolute_import, unicode_literals
from celery import task


@task()
def task_number_one():
    print("I am task one!")

@task
def task_number_two():
    with open("1.txt", "a") as f:
        f.write("I was here!\n")
