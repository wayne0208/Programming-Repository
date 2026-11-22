import model


def f5(course):
    must_class = input("必修清單(課堂代號之間用空白隔開):").split()
    hope_class = input("希望修習的課程(課堂代號之間用空白隔開):").split()
    min_credits = int(input("最低學分:"))
    max_credits = int(input("最高學分:"))
    not_time = input("不可上課的時段(EX1-1)(之間用空白隔開):").split()
    preference_time = input("偏好上課的星期(數字之間用空白隔開):").split()
    error = []  # 存放導致「可行性失敗」
    cant = []  # 存放「提醒」

    # 必修希望課程都有填
    if must_class and hope_class:
        index_must_class = index_class(must_class, course)  # 課堂順序代號
        index_hope_class = index_class(hope_class, course)

        OKcap_must_class, notcap_must_class = check_OK_capacity(index_must_class, course)
        OKcap_hope_class, notcap_hope_class = check_OK_capacity(index_hope_class, course)  # 回傳課代碼
        if notcap_must_class:
            for i in notcap_must_class:
                error.append(f"必修課程{i}人數已額滿")
        if notcap_hope_class:
            for i in notcap_hope_class:
                cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_must_class = check_not_time(not_time, index_must_class, course)  # 不可上課時段時間去掉
        OKtime_hope_class = check_not_time(not_time, index_hope_class, course)  # 回傳課代碼
        for i in must_class:
            if i not in OKtime_must_class:
                error.append(f"必修課程{i}在不可上課時段")
        for i in hope_class:
            if i not in OKtime_hope_class:
                cant.append(f"希望修習的課程{i}在不可上課時段")
        OKpre_must_class = check_preference(index_must_class, preference_time, course)  # 偏好星期
        OKpre_hope_class = check_preference(index_hope_class, preference_time, course)
        for i in must_class:
            if i not in OKpre_must_class:
                error.append(f"必修課程{i}不在偏好星期")
        for i in hope_class:
            if i not in OKpre_hope_class:
                cant.append(f"希望修習的課程{i}不在偏好星期")
        OK_must = set(OKcap_must_class) & set(OKtime_must_class) & set(OKpre_must_class)
        final_must = [c for c in must_class if c in OK_must]

        OK_hope = set(OKcap_hope_class) & set(OKtime_hope_class) & set(OKpre_hope_class)

        final_hope = [c for c in hope_class if c in OK_hope]

    # 只填必修
    elif must_class and not hope_class:

        index_must_class = index_class(must_class, course)
        OKcap_must_class, notcap_must_class = check_OK_capacity(index_must_class, course)
        if notcap_must_class:
            for i in notcap_must_class:
                error.append(f"必修課程{i}人數已額滿")

        OKtime_must_class = check_not_time(not_time, index_must_class, course)
        for i in must_class:
            if i not in OKtime_must_class:
                error.append(f"必修課程{i}在不可上課時段")
        OKpre_must_class = check_preference(index_must_class, preference_time, course)  # 偏好星期
        for i in must_class:
            if i not in OKpre_must_class:
                error.append(f"必修課程{i}不在偏好星期")
        OK_must = set(OKcap_must_class) & set(OKtime_must_class) & set(OKpre_must_class)
        final_must = [c for c in must_class if c in OK_must]
        other_courses = [c[0] for c in course if c[0] not in must_class]

        index_other = index_class(other_courses, course)
        ok_cap_other, _ = check_OK_capacity(index_other, course)
        ok_time_other = check_not_time(not_time, index_other, course)
        ok_pre_other = check_preference(index_other, preference_time, course)
        ok_other = set(ok_cap_other) & set(ok_time_other) & set(ok_pre_other)
        final_hope = [c for c in other_courses if c in ok_other]

    # 只填希望課程
    elif not must_class and hope_class:
        index_hope_class = index_class(hope_class, course)
        OKcap_hope_class, notcap_hope_class = check_OK_capacity(index_hope_class, course)
        if notcap_hope_class:
            for i in notcap_hope_class:
                cant.append(f"希望修習的課程{i}人數已額滿")
        OKtime_hope_class = check_not_time(not_time, index_hope_class, course)
        for i in hope_class:
            if i not in OKtime_hope_class:
                cant.append(f"希望修習的課程{i}在不可上課時段")
        OKpre_hope_class = check_preference(index_hope_class, preference_time, course)  # 偏好星期
        for i in hope_class:
            if i not in OKpre_hope_class:
                cant.append(f"希望修習的課程{i}不在偏好星期")

        OK_hope = set(OKcap_hope_class) & set(OKtime_hope_class) & set(OKpre_hope_class)
        final_hope = [c for c in hope_class if c in OK_hope]

    # 都沒填
    else:
        class_ = [i[0] for i in course]
        index_class_ = index_class(class_, course)
        ok_cap_class_, _ = check_OK_capacity(index_class_, course)
        ok_time_class_ = check_not_time(not_time, index_class_, course)
        ok_pre_class_ = check_preference(index_class_, preference_time, course)
        ok_class_ = set(ok_cap_class_) & set(ok_time_class_) & set(ok_pre_class_)
        final_hope = [c for c in class_ if c in ok_class_]

    if len(final_must) > 1:  # 必修衝堂檢查
        index_ = index_class(final_must, course)
        for i in range(len(index_)):
            for j in range(i + 1, len(index_)):
                k = set(course[index_[i]][8]) & set(course[index_[j]][8])
                if k:
                    s = f"必修課程{course[index_[i]][0]}與{course[index_[j]][0]}衝堂 {k}"
                    error.append(s)

    # 學分計算
    ffin_class = list(final_must)
    total_credits = 0
    total_credits = sum([course[i][2] for i in index_class(final_must, course)])
    # 計算時段(合集)
    fin_slots = set()
    for i in index_class(final_must, course):
        fin_slots = set(course[i][8]) | fin_slots
    if total_credits > max_credits:
        error.append(f"必修課程學分{total_credits}超過最高學分{max_credits}")
    else:
        for i in final_hope:
            ind = index_class([i], course)
            cre = course[ind[0]][2]
            slo = set(course[ind[0]][8])
            # 檢查衝堂
            if fin_slots & slo:
                if hope_class:
                    cant.append(f"希望修習的課程{i}與必修課程衝堂")
                continue
            if total_credits + cre <= max_credits:
                total_credits += cre
                fin_slots = fin_slots | slo
                ffin_class.append(i)
            else:
                if hope_class:
                    cant.append(f"希望修習的課程{i}學分超過最高學分{max_credits}")
    if total_credits < min_credits:
        error.append(f"總學分{total_credits}低於最低學分{min_credits}")

    # 輸出結果
    print("\n========== 可行性檢查結果 ==========")
    if cant:
        print("提醒：")
        for c in cant:
            print("- " + c)
    if error:
        print("可行性失敗，原因如下：")
        for e in error:
            print("- " + e)
    else:
        print("可行性成功，選課結果如下：")
        print(f"總學分：{total_credits}")
        for idx in index_class(ffin_class, course):
            c = course[idx]
            print(f"   - {c[0]} | {c[1]} | {c[2]}學分 | {c[3]} | 教師:{c[4]} | 時段:{','.join(c[8])}")
            print("======================================================")


def check_preference(_index, preference_time, course):  # 偏好星期
    time_ = []
    for i in _index:
        if not preference_time:
            time_.append(course[i][0])  # 回傳課代碼
            continue
        t = True
        for j in range(len(course[i][8])):
            if course[i][8][j][0] not in preference_time:
                t = False
        if t:
            time_.append(course[i][0])  # 回傳課代碼
    return time_


def index_class(_class, course):  # 課堂順序代號
    index_ = []
    for i in range(len(course)):
        if course[i][0] in _class:
            index_.append(i)
    return index_


def check_not_time(not_time, _index, course):  # 不可上課時段時間去掉
    OK_class = []
    for i in _index:
        t = True
        for j in range(len(course[i][8])):

            if course[i][8][j] in not_time:
                t = False
        if t:
            OK_class.append(course[i][0])
    return OK_class  # 回傳課代碼


def check_OK_capacity(_index, course):  # 人數尚未額滿
    OK_class = []
    Not_class = []
    for i in _index:
        if course[i][5] > course[i][6]:  # 沒超過人數限制
            OK_class.append(course[i][0])  # 回傳課代碼
        else:
            Not_class.append(course[i][0])
    return OK_class, Not_class


def error_capacity(class1, class2, course):  # 必修清單衝堂
    index1 = index_class(class1, course)  # 假設是必修
    index2 = index_class(class2, course)
    over = []
    for i in index1:
        for j in index2:
            if i == j:
                continue
            k = set(course[i][8]) & set(course[j][8])
            if k:
                s = f"必修課程{course[i][0]}與希望修習的課程{course[j][0]}衝堂 {k}"
                if s not in over:
                    over.append(s)
    return over


def main():
    course, _, _, _ = model.data()  # _==students,activitys,classroom
    f5(course)


if __name__ == "__main__":
    main()
