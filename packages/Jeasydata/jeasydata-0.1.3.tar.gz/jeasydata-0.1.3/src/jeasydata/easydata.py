import re
import threading
import tkinter as tk
pattern = re.compile(r"\[(.*?)\]\s*:\s*(.*?)\s*;")
dataOut = [] # brednie
saved = []  #zapisae tylko wyjście

DataOnly = []  #zapisae tylko wyjście
TargetOnly = []  #zapisae tylko start

def delete(val1, filename):
    # matches: [apple]: anything;
    pattern = re.compile(rf"^\s*\[{re.escape(val1)}\]\s*:\s*.*?;\s*$")

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    removed_count = 0

    for line in lines:
        if pattern.match(line):
            removed_count += 1
            continue
        new_lines.append(line)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return removed_count

def decode(file):
    with open(file, "rb") as f:
        data = f.read()

    if not data:
        return  # empty file, nothing to decode

    data = data[1:]  # remove first byte

    with open(file, "wb") as f:
        f.write(data)
  # write one byte   

def encode(file):
    with open(file, "r+b") as f:
        f.write(b'\x01')   # write one byte


def int_read():
    read("file.JBK")
    print("reading done, out: ")
    print(dataOut)
    return dataOut
def read(file):
    try:
        with open(file, "r", encoding="utf-8") as file:
            for line in file:
                match = pattern.search(line)
                if match:
                    firstValue = match.group(1)
                    secondValue = match.group(2)
                    dataOut.append(firstValue)
                    dataOut.append("@"+ secondValue)
                    
    except Exception as e:
        return
    return dataOut
        
    
def target(target_name,file):
    if dataOut == []:
        read(file)
    start_saving = False
    local_saved = []
    try:
        for item in dataOut:
            if not start_saving:
                if item == target_name:
                    start_saving = True
                continue  # keep scanning until we hit the target

            # after target:
            if item.startswith("@"):
                local_saved.append(item[1:])  # remove '@'
            else:
                break  # next target reached -> stop

        return local_saved
    except Exception as e:
        return


def readAll(file):
    try:
        dataOut.clear()
        TargetOnly.clear()
        DataOnly.clear()

        read(file)

        for item in dataOut:
            if item.startswith("@"):
                DataOnly.append(item[1:])   # remove '@'
            else:
                TargetOnly.append(item)

        print(TargetOnly, DataOnly)
        return TargetOnly, DataOnly
    except Exception as e:
        return

def readAllTargets(file):
    if not TargetOnly:
        readAll(file)

    results = {}

    for item in TargetOnly:
        results[item] = target(item, file)

    return results


def save(val1, val2, filename):
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{val1}]: {val2};\n")
    except Exception as e:
        return
 
def debug(file):
    x = input("Function :> ")
    if x == "read":
        int_read()
        debug(file)
    elif x == "target":
        y = input("target :> ")
        target(y)
        debug(file)
    if x == "read all":
        readAll(file)
        debug(file)

