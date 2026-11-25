from datamodel import Course


def f5(
    course: dict[str, Course],
    must_clas: list[str] | None = None,
    hope_clas: list[str] | None = None,
    min_credits: int = 0,
    max_credits: int = 100,
    not_time: list[str] | None = None,
    preference_time: list[str] | None = None,
) -> dict:
    must_class = must_clas or []
    hope_class = hope_clas or []
    not_time_list = not_time or []
    pref_time_list = preference_time or []

    error: list[str] = []       # 存放導致「可行性失敗」
    cant: list[str] = []        # 存放「提醒」
    final_must: list[str] = []
    final_hope: list[str] = []

    # 必修希望課程都有填
    if must_class and hope_class:
        ok_cap_must_class, not_cap_must_class = check_ok_capacity(must_class, course)
        ok_cap_hope_class, not_cap_hope_class = check_ok_capacity(hope_class, course)

        for i in not_cap_must_class:
            error.append(f"必修課程{i}人數已額滿")
        for i in not_cap_hope_class:
            cant.append(f"希望修習的課程{i}人數已額滿")

        ok_time_must_class = check_not_time(not_time_list, must_class, course)
        ok_time_hope_class = check_not_time(not_time_list, hope_class, course)
        for i in must_class:
            if i not in ok_time_must_class and i in course:
                error.append(f"必修課程{i}在不可上課時段")
        for i in hope_class:
            if i not in ok_time_hope_class and i in course:
                cant.append(f"希望修習的課程{i}在不可上課時段")

        ok_pre_must_class = check_preference(must_class, pref_time_list, course)
        ok_pre_hope_class = check_preference(hope_class, pref_time_list, course)
        for i in must_class:
            if i not in ok_pre_must_class and i in course:
                error.append(f"必修課程{i}不在偏好星期")
        for i in hope_class:
            if i not in ok_pre_hope_class and i in course:
                cant.append(f"希望修習的課程{i}不在偏好星期")

        # 檢查不存在的課程代碼
        for i in must_class:
            if i not in course:
                error.append(f"必修課程{i}不存在")
        for i in hope_class:
            if i not in course:
                cant.append(f"希望修習的課程{i}不存在")

        ok_must = set(ok_cap_must_class) & set(ok_time_must_class) & set(ok_pre_must_class)
        final_must = [c for c in must_class if c in ok_must]

        ok_hope = set(ok_cap_hope_class) & set(ok_time_hope_class) & set(ok_pre_hope_class)
        final_hope = [c for c in hope_class if c in ok_hope]

    # 只填必修
    elif must_class and not hope_class:
        ok_cap_must_class, not_cap_must_class = check_ok_capacity(must_class, course)
        for i in not_cap_must_class:
            error.append(f"必修課程{i}人數已額滿")

        ok_time_must_class = check_not_time(not_time_list, must_class, course)
        for i in must_class:
            if i not in ok_time_must_class and i in course:
                error.append(f"必修課程{i}在不可上課時段")

        ok_pre_must_class = check_preference(must_class, pref_time_list, course)
        for i in must_class:
            if i not in ok_pre_must_class and i in course:
                error.append(f"必修課程{i}不在偏好星期")

        for i in must_class:
            if i not in course:
                error.append(f"必修課程{i}不存在")

        ok_must = set(ok_cap_must_class) & set(ok_time_must_class) & set(ok_pre_must_class)
        final_must = [c for c in must_class if c in ok_must]

        other_courses = [c for c in course if c not in must_class]
        ok_cap_other, _ = check_ok_capacity(other_courses, course)
        ok_time_other = check_not_time(not_time_list, other_courses, course)
        ok_pre_other = check_preference(other_courses, pref_time_list, course)
        ok_other = set(ok_cap_other) & set(ok_time_other) & set(ok_pre_other)
        final_hope = [c for c in other_courses if c in ok_other]

    # 只填希望課程
    elif not must_class and hope_class:
        ok_cap_hope_class, not_cap_hope_class = check_ok_capacity(hope_class, course)
        for i in not_cap_hope_class:
            cant.append(f"希望修習的課程{i}人數已額滿")

        ok_time_hope_class = check_not_time(not_time_list, hope_class, course)
        for i in hope_class:
            if i not in ok_time_hope_class and i in course:
                cant.append(f"希望修習的課程{i}在不可上課時段")

        ok_pre_hope_class = check_preference(hope_class, pref_time_list, course)
        for i in hope_class:
            if i not in ok_pre_hope_class and i in course:
                cant.append(f"希望修習的課程{i}不在偏好星期")

        for i in hope_class:
            if i not in course:
                cant.append(f"希望修習的課程{i}不存在")

        ok_hope = set(ok_cap_hope_class) & set(ok_time_hope_class) & set(ok_pre_hope_class)
        final_hope = [c for c in hope_class if c in ok_hope]

    # 都沒填
    else:
        class_ = list(course.keys())
        ok_cap_class_, _ = check_ok_capacity(class_, course)
        ok_time_class_ = check_not_time(not_time_list, class_, course)
        ok_pre_class_ = check_preference(class_, pref_time_list, course)
        ok_class_ = set(ok_cap_class_) & set(ok_time_class_) & set(ok_pre_class_)
        final_hope = [c for c in class_ if c in ok_class_]

    # 必修衝堂檢查
    if len(final_must) > 1:
        for i in range(len(final_must)):
            for j in range(i + 1, len(final_must)):
                c1 = course[final_must[i]]
                c2 = course[final_must[j]]
                k = set(c1.slots) & set(c2.slots)
                if k:
                    s = f"必修課程{c1.code}與{c2.code}衝堂 {sorted(k)}"
                    error.append(s)

    # 學分計算
    ffin_class = list(final_must)
    total_credits = sum([course[i].credits for i in final_must])

    # 計算時段(合集)
    fin_slots: set[str] = set()
    for i in final_must:
        fin_slots = set(course[i].slots) | fin_slots

    if total_credits > max_credits:
        error.append(f"必修課程學分{total_credits}超過最高學分{max_credits}")
    else:
        for i in final_hope:
            ind = course[i]
            cre = ind.credits
            slo = set(ind.slots)
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
    return {
        "ok": len(error) == 0,
        "selected_courses": [course[code] for code in ffin_class],
        "total_credits": total_credits,
        "error": error,
        "cant": cant,
    }


def check_preference(codes: list[str], preference_time: list[str], course: dict[str, Course]) -> list[str]:
    time_ = []
    for i in codes:
        c = course.get(i)
        if c is None:
            continue
        if not preference_time:
            time_.append(i)
            continue
        if all(slot[0] in preference_time for slot in c.slots):
            time_.append(i)
    return time_


def check_not_time(not_time: list[str], codes: list[str], courses: dict[str, Course]) -> list[str]:
    ok_class = []
    for code in codes:
        c = courses.get(code)
        if c is None:
            continue
        if all(slot not in not_time for slot in c.slots):
            ok_class.append(code)
    return ok_class


def check_ok_capacity(codes: list[str], courses: dict[str, Course]) -> tuple[list[str], list[str]]:
    ok_class = []
    not_class = []
    for code in codes:
        c = courses.get(code)
        if c is None:
            continue
        if c.capacity > c.enrolled:
            ok_class.append(code)
        else:
            not_class.append(code)
    return ok_class, not_class

"""
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
    return over"""

"""
def main():
    course, _, _, _ = model.data()  # _==students,activitys,classroom
    f5(course)"""

"""
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
            print("======================================================")"""
#if __name__ == "__main__":

