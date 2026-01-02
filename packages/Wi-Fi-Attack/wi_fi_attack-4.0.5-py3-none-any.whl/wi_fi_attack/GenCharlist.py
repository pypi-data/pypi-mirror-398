def load_lists():
    list = ['!','@','-','_','=','#','$','%','^','&','*','(',')','.','"',"'","|","{","}",",","<",">","~","`",""]
    list_2 = []
    list_3 = []
    list_4 = []
    for i in range(len(list)):
        list_2.append(list[i]*2)
        list_3.append(list[i]*3)
        list_4.append(list[i]*4)
    return list,list_2,list_3,list_4
def generate_password(partofpassword,filename):
    l1,l2,l3,l4 = load_lists()
    list_to_file = []
    lists = [l1,l2,l3,l4]
    for var in lists:
        for char in range(len(var)):
            first = var[char] + partofpassword + var[char]
            second = var[char] + partofpassword
            third = partofpassword + var[char]
            list_to_file.append(first)
            list_to_file.append(second)
            list_to_file.append(third)
    with open(filename,"w") as f:
        for item in list_to_file:
            f.write(item + '\n')
    choice = input("Wanna view them? Type 'yes' or press Enter to skip: ")
    if choice.lower() == "yes":
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            print(lines)

    print("Bye!")
