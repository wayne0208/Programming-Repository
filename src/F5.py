import model
def f5():
    course,_,_,_=model.data()#_==students,activitys,classroom
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
    error=[]# 存放導致「可行性失敗」
    cant=[]# 存放「提醒」

    #必修希望課程都有填
    if must_class and hope_class:
        index_must_class=index_class(must_class,course)#課堂順序代號
        index_hope_class=index_class(hope_class,course)

        OKcap_must_class,notcap_must_class=check_OK_capacity(index_must_class,course)
        OKcap_hope_class,notcap_hope_class=check_OK_capacity(index_hope_class,course)#回傳課代碼
        if  notcap_must_class:
             for i in notcap_must_class:
                  error.append(f"必修課程{i}人數已額滿")
        if  notcap_hope_class:
                for i in notcap_hope_class:
                    cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_must_class=check_not_time(not_time,index_must_class,course)#不可上課時段時間去掉
        OKtime_hope_class=check_not_time(not_time,index_hope_class,course)#回傳課代碼
        for i in must_class:
             if i not in OKtime_must_class:
                  error.append(f"必修課程{i}在不可上課時段")
        for i in hope_class:
             if i not in OKtime_hope_class:
                  cant.append(f"希望修習的課程{i}在不可上課時段")
        OKpre_must_class=check_preference(index_must_class,preference_time,course)#偏好星期
        OKpre_hope_class=check_preference(index_hope_class,preference_time,course)
        for i in must_class:
             if i not in OKpre_must_class:
                  error.append(f"必修課程{i}不在偏好星期")
        for i in hope_class:
             if i not in OKpre_hope_class:
                  cant.append(f"希望修習的課程{i}不在偏好星期")
        OK_must=set(OKcap_must_class)&set(OKtime_must_class)&set(OKpre_must_class)
        final_must = [c for c in must_class if c in OK_must]

        OK_hope=set(OKcap_hope_class)&set(OKtime_hope_class)&set(OKpre_hope_class)
        # 把衝堂的希望課移除
        conflicts = error_capacity(final_must, list(OK_hope), course)
        if conflicts:
            cant.extend(conflicts)
            for m_idx in index_class(final_must, course):
                for h_code in list(OK_hope):
                    h_idx = index_class([h_code], course)
                    if set(course[m_idx]) & set(course[h_idx]):
                        OK_hope.discard(h_code)
        final_hope = [c for c in hope_class if c in OK_hope]

#只填必修
    elif must_class and not hope_class:

        index_must_class=index_class(must_class,course)
        OKcap_must_class,notcap_must_class=check_OK_capacity(index_must_class,course)
        if  notcap_must_class:
            for i in notcap_must_class:
                error.append(f"必修課程{i}人數已額滿")


        OKtime_must_class=check_not_time(not_time,index_must_class,course)
        for i in must_class:
             if i not in OKtime_must_class:
                  error.append(f"必修課程{i}在不可上課時段")
        OKpre_must_class=check_preference(index_must_class,preference_time,course)#偏好星期
        for i in must_class:
             if i not in OKpre_must_class:
                  error.append(f"必修課程{i}不在偏好星期")
        OK_must=set(OKcap_must_class)&set(OKtime_must_class)&set(OKpre_must_class)
        final_must = [c for c in must_class if c in OK_must]
        other_courses = [c for c in course if c not in must_class]

        index_other=index_class(other_courses,course)
        ok_cap_other,_=check_OK_capacity(index_other,course)
        ok_time_other=check_not_time(not_time,index_other,course)
        ok_pre_other=check_preference(index_other,preference_time,course)
        ok_other=set(ok_cap_other)&set(ok_time_other)&set(ok_pre_other)
        final_hope= [c for c in other_courses if c in ok_other]

#只填希望課程
    elif not must_class and hope_class:
        index_hope_class=index_class(hope_class,course)
        OKcap_hope_class,notcap_hope_class=check_OK_capacity(index_hope_class,course)
        if  notcap_hope_class:
                for i in notcap_hope_class:
                    cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_hope_class=check_not_time(not_time,index_hope_class,course)
        for i in hope_class:
             if i not in OKtime_hope_class:
                  cant.append(f"希望修習的課程{i}在不可上課時段")
        OKpre_hope_class=check_preference(index_hope_class,preference_time,course)#偏好星期
        for i in hope_class:
             if i not in OKpre_hope_class:
                  cant.append(f"希望修習的課程{i}不在偏好星期")

        OK_hope=set(OKcap_hope_class)&set(OKtime_hope_class)&set(OKpre_hope_class)
        final_hope = [c for c in hope_class if c in OK_hope]
#都沒填
    else:
        class_=[i for i in course]
        index_class_=index_class(class_,course)
        ok_cap_class_,_=check_OK_capacity(index_class_,course)
        ok_time_class_=check_not_time(not_time,index_class_,course)
        ok_pre_class_=check_preference(index_class_,preference_time,course)
        ok_class_=set(ok_cap_class_)&set(ok_time_class_)&set(ok_pre_class_)
        final_hope= [c for c in class_ if c in ok_class_]

    if len(final_must)>1:#必修衝堂檢查
          index_=index_class(final_must,course)
          for i in range(len(index_)):
               for j in range(i+1,len(index_)):
                    k= set(course[index_[i]][8]) & set(course[index_[j]][8])
                    if k:
                        s=f"必修課程{course[i][0]}與{course[j][0]}衝堂 {k}"
                        error.append(s)
#學分計算
                         

def check_preference(_index,preference_time,course):#偏好星期
     time_=[]
     for i in _index:
        if not preference_time:
             time_.append(course[i][0])#回傳課代碼
             continue
        t=True
        for j in range(len(course[i][8])):
             if course[i][8][j][0] not in preference_time:
                  t=False
        if t:
             time_.append(course[i][0])#回傳課代碼
     return time_
     

def index_class(_class,course):#課堂順序代號
    index_=[]
    for i in range(len(course)):
                if course[i][0] in _class:
                    index_.append(i)
    return index_
def check_not_time(not_time,_index,course):#不可上課時段時間去掉
    OK_class=[]
    for i in _index:
        t=True
        for j in range(len(course[i][8])):
            
            if course[i][8][j]  in not_time:
                 t=False
        if t:
            OK_class.append(course[i][0])
    return OK_class#回傳課代碼

def check_OK_capacity(_index,course):#人數尚未額滿
    OK_class=[]
    Not_class=[]
    for i in _index:
        if course[i][5]>course[i][6]: #沒超過人數限制
            OK_class.append(course[i][0])#回傳課代碼
        else:
             Not_class.append(course[i][0])
    return OK_class,Not_class
def error_capacity(class1,class2,course):#必修清單衝堂
    index1=index_class(class1,course)#假設是必修
    index2=index_class(class2,course)
    over=[]
    for i in index1:
        for j in index2:
            if i == j:
                 continue
            k= set(course[i][8]) & set(course[j][8])
            if k:
                 s=f"必修課程{course[i][0]}與希望修習的課程{course[j][0]}衝堂 {k}"
                 if s not in over:
                    over.append(s)
    return over
f5()