from PIL import Image
from time import time
from math import log2
from pathlib import Path

def get_bin(n):
    return bin(n)[2:]

def is_encodable(_bytes,img,n_weak):
    to_encode = 8*len(_bytes)
    encodable = int((n_weak/8)*(24*img.width*img.height))
    return to_encode < encodable


def split(byte,n_weak=1):
    strong = byte>>n_weak<<n_weak
    weak = byte-strong
    return strong,weak

#former version
def group(byte,n_weak=1,size=8):
    length = size//n_weak
    liste = []
    left = byte
    for i in range(length):
        liste.append(left>>(size-(i+1)*n_weak))
        left = left - (left>>(size-(i+1)*n_weak)<<(size-(i+1)*n_weak))
    return liste

        
def get_bytes_series(_bytes,n_weak):
    print("Traitement du fichier...")
    series = []
    if 8%n_weak != 0:
        raise ValueError("Must select between 1,2,4 and 8")
    length = (8//n_weak)*len(_bytes) + 32//n_weak  + 2

    encode_n_weak = int(log2(n_weak))

    series.extend(group(encode_n_weak,1)[-2:])
    length_list = group(length,n_weak,size=32)
    while len(length_list) < 32//n_weak:
        length_list = [0]+length_list
    series.extend(length_list)
    len_bytes = len(_bytes)
    n_parsed = 0
    for byte in _bytes:
        new_seq = group(byte,n_weak)
        series.extend(new_seq)
        n_parsed += 1
        prct = n_parsed/len_bytes
        if prct>1:
            prct = 1
        print("\r|"+round(prct*50)*"-"+round((1-prct)*50)*" "+"|"+f"{round(prct*100)}%",end = "")
    print("\n")
    return series



def file_encode(img_path,file_path,n_weak=1):
    img = Image.open(img_path)
    with open(file_path,"rb") as file:
        _bytes = file.read()
    while not is_encodable(_bytes,img,n_weak):
        n_weak *= 2
        if n_weak > 8:
            print("Le fichier est trop lourd par rapport à l'image que vous souhaitez utiliser.")
            print("Vous pouvez essayer d'utiliser une image plus grande, ou de compresser votre fichier.")
            return None
    print(f"{n_weak} bits par octet seront surchargés (moins il y en a, plus la stéganographie est discrète)")
    if n_weak >= 4:
        print("ATTENTION : LA STEGANOGRAPHIE SERA CERTAINEMENT VISIBLE")
    series = get_bytes_series(_bytes,n_weak)
    print("Ecriture des données...")

    n_encoded = 0
    l = len(series)
    for x in range(img.width):
        for y in range(img.height):
            colors = list(img.getpixel((x,y)))
            for color in colors:
                if n_encoded < l:
                    if n_encoded < 2:
                        strong,weak = split(color,1)
                    else:
                        strong,weak = split(color,n_weak)
                    colors[n_encoded%3] = strong + series[n_encoded]
                    n_encoded += 1
                else:
                    img.putpixel((x,y),tuple(colors))
                    print("\n")
                    return img
            img.putpixel((x,y),tuple(colors))
            prct = n_encoded/l
            if prct>1:
                prct = 1
            print("\r|"+round(prct*50)*"-"+round((1-prct)*50)*" "+"|"+f'{round(prct*100)}%',end = "")
    print('\n')
    return img



def file_decode(path,dest):
    if type(path) is str:
        img = Image.open(path)
    else:
        img = path

    message = bytearray()

    n_decoded = 0
    last_weak = 0
    length = 0
    finished = False
    len_length = 0
    start_message = 0
    n_weak = 0
    print("Traitement de l'image...")
    for x in range(img.width):
        if finished:
            break
        for y in range(img.height):
            colors = list(img.getpixel((x,y)))
            for color in colors:
                if n_decoded < 2:
                    strong,weak = split(color,1)
                else:
                    strong,weak = split(color,n_weak)
                if n_decoded < 1:
                    n_weak <<= 1
                    n_weak += weak
                elif n_decoded == 1:
                    n_weak <<= 1
                    n_weak += weak
                    n_weak = 2**n_weak
                elif n_decoded < (32//n_weak)+1:
                    length <<= n_weak
                    length += weak
                elif n_decoded == (32//n_weak)+1:
                    length<<=n_weak
                    length += weak
                    start_message = n_decoded
                elif (n_decoded-start_message)%(8//n_weak) != 0:
                    last_weak <<= n_weak
                    last_weak += weak
                else:
                    last_weak <<= n_weak
                    binary = last_weak + weak
                    last_weak = 0
                    if n_decoded < length:
                        message.append(binary)
                    else:
                        finished = True
                n_decoded += 1
            if start_message != 0:
                prct = n_decoded/length
                if prct>1:
                    prct = 1
                print("\r|"+round(prct*50)*"-"+round((1-prct)*50)*" "+"|"+f'{round(prct*100)}%',end = "")
    print("\n")
    with open(dest,mode = "wb") as file:
        n_written = file.write(message)
    return message,n_written

while True:
    print("Voulez-vous stéganographier un document (e), décoder une image stéganographiée (d) ou quitter l'application (q)?")

    choice = input()

    while not choice in ("e","d","q"):
        print("Veuillez choisir entre \"e\" (encoder), \"d\" (décoder) et \"q\" (quitter).")
        choice = input()

    if choice == "q":
        break

    elif choice == "e":
        print("Quelle image voulez-vous utiliser comme support ? (donnez un chemin absolu)")
        src_img = input()
        finished = False
        while not finished:
            if Path(src_img).exists():
                finished = True
            else:
                print()
                print("Le fichier n'exite pas. Peut-être avez-vous fait une faute de frappe ou donné un chemin relatif ?")
                src_img = input()
            dest_img = src_img.split(".")[0]+" stéganographié."+src_img.split(".")[1]
        print("Quel fichier voulez-vous stéganographier ? (donnez un chemin absolu)")
        src_file = input()
        finished = False
        while not finished:
            if Path(src_file).exists():
                finished = True
            else:
                print()
                print("Le fichier n'exite pas. Peut-être avez-vous fait une faute de frappe ou donné un chemin relatif ?")
                src_file = input()
        print("Que priviligiez-vous : la qualité de la stéganographie (1) ou la vitesse d'écriture (2) ?")
        choice2 = input()
        if choice2 == "1":
            new_img = file_encode(src_img,src_file)
        elif choice2 == "2":
            new_img = file_encode(src_img,src_file,2)
        if new_img is None:
            continue
        print("sauvegarde de l'image stéganographiée...")
        new_img.save(dest_img)
        if "\\" in dest_img:
            name = dest_img.split('\\')[-1]
            print(f"Et voilà ! l'image \"{name}\" a maintenant été générée dans le dossier de l'image support !")
        else:
            print(f"Et voilà ! l'image \"{dest_img.split('/')[-1]}\" a maintenant été générée dans le dossier de l'image support !")
        print()
        print("Pensez à la renommer, pour éviter de griller votre couverture....")
        print()
    elif choice == "d":
        print("Quelle image voulez-vous décoder ? (donnez un chemin absolu)")
        src_img = input()
        finished = False
        while not finished:
            if Path(src_img).exists():
                finished = True
            else:
                print()
                print("Le fichier n'exite pas. Peut-être avez-vous fait une faute de frappe ou donné un chemin relatif ?")
                src_img = input()

        dest_img = src_img.split(".")[0]+" stéganographié."+src_img.split(".")[1]
        print("Quel fichier voulez-vous utiliser pour réceptionner les données ? (donnez un chemin absolu)")
        dest_file = input()

        message,n_written  = file_decode(src_img,dest_file)
        print("Et voilà ! Votre fichier doit maintenant être décodé.")
