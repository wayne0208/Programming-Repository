import model
def f5():
    must_class0=input("必修清單(課堂代號之間用空白隔開):")
    must_class=must_class0.split()
    hope_class0=input("希望修習的課程(課堂代號之間用空白隔開):")
    hope_class=hope_class0.split()
    min_credits=input("最低學分:")
    min_credits=int(min_credits)if min_credits else 0
    max_credits=input("最高學分:")
    max_credits=int(max_credits)if max_credits else 100
    not_time=input("不可上課的時段(EX1-1)(之間用空白隔開):")
    not_time=not_time.split()
    preference_time=input("偏好上課的星期(數字之間用空白隔開):")
    preference_time=preference_time.split()
    error=[]
    cant=[]
    if must_class and hope_class:
        index_must_class=index_class(must_class)#課堂順序代號
        index_hope_class=index_class(hope_class)

        OKcap_must_class,notcap_must_class=check_OK_capacity(index_must_class)
        OKcap_hope_class,notcap_hope_class=check_OK_capacity(index_hope_class)#回傳課代碼
        if  notcap_must_class:
             for i in notcap_must_class:
                  error.append(f"必修課程{i}人數已額滿")
        if  notcap_hope_class:
                for i in notcap_hope_class:
                    cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_must_class=check_not_time(not_time,index_must_class)#不可上課時段時間去掉
        OKtime_hope_class=check_not_time(not_time,index_hope_class)#回傳課代碼
        for i in must_class:
             if i not in OKtime_must_class:
                  error.extend(f"必修課程{i}在不可上課時段")
        for i in hope_class:
             if i not in OKtime_hope_class:
                  cant.extend(f"希望修習的課程{i}在不可上課時段")
        OKpre_must_class=check_preference(index_must_class,preference_time)#偏好星期
        OKpre_hope_class=check_preference(index_hope_class,preference_time)
        for i in must_class:
             if i not in OKpre_must_class:
                  error.append(f"必修課程{i}不在偏好星期")
        for i in hope_class:
             if i not in OKpre_hope_class:
                  cant.append(f"希望修習的課程{i}不在偏好星期")
        error.append(error_capacity(OKtime_must_class,OKtime_hope_class))#衝堂檢查
        


    elif must_class and not hope_class:

        index_must_class=index_class(must_class)
        OKcap_must_class,notcap_must_class=check_OK_capacity(index_must_class)
        if  notcap_must_class:
            for i in notcap_must_class:
                error.append(f"必修課程{i}人數已額滿")


        OKtime_must_class=check_not_time(not_time,index_must_class)
        for i in must_class:
             if i not in OKtime_must_class:
                  error.extend(f"必修課程{i}在不可上課時段")
        OKpre_must_class=check_preference(index_must_class,preference_time)#偏好星期
        for i in must_class:
             if i not in OKpre_must_class:
                  error.append(f"必修課程{i}不在偏好星期")



    elif not must_class and hope_class:
        index_hope_class=index_class(hope_class)
        OKcap_hope_class,notcap_hope_class=check_OK_capacity(index_hope_class)
        if  notcap_hope_class:
                for i in notcap_hope_class:
                    cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_hope_class=check_not_time(not_time,index_hope_class)
        for i in hope_class:
             if i not in OKtime_hope_class:
                  cant.extend(f"希望修習的課程{i}在不可上課時段")
        OKpre_hope_class=check_preference(index_hope_class,preference_time)#偏好星期
        for i in hope_class:
             if i not in OKpre_hope_class:
                  cant.append(f"希望修習的課程{i}不在偏好星期")

    else:
        class_=[i for i in model.course]

def check_preference(_index,preference_time):#偏好星期
     time_=[]
     for i in _index:
        if not preference_time:
             time_.append(model.course[i][0])#回傳課代碼
             continue
        t=True
        for j in range(len(model.course[i][8])):
             if model.course[i][8][j][0] not in preference_time:
                  t=False
        if t:
             time_.append(model.course[i][0])#回傳課代碼
     return time_
     

def index_class(_class):#課堂順序代號
    index_=[]
    for i in range(len(model.course)):
                if model.course[i][0] in _class:
                    index_.append(i)
    return index_
def check_not_time(not_time,_index):#不可上課時段時間去掉
    OK_class=[]
    for i in _index:
        t=True
        for j in range(len(model.course[i][8])):
            
            if model.course[i][8][j]  in not_time:
                 t=False
        if t:
            OK_class.append(model.course[i][0])
    return OK_class#回傳課代碼

def check_OK_capacity(_index):#人數尚未額滿
    OK_class=[]
    Not_class=[]
    for i in _index:
        if model.course[i][5]>model.course[i][6]: #沒超過人數限制
            OK_class.append(model.course[i][0])#回傳課代碼
        else:
             Not_class.append(model.course[i][0])
    return OK_class,Not_class
def error_capacity(class1,class2):#必修清單衝堂
    index1=index_class(class1)#假設是必修
    index2=index_class(class2)
    over=[]
    for i in index1:
        for j in index2:
            if i == j:
                 continue
            k= set(model.course[i][8]) & set(model.course[j][8])
            if k:
                 s=f"必修課程{model.course[i][0]}與希望修習的課程{model.course[j][0]}衝堂 {k}"
                 if s not in over:
                    over.append(s)
    return over