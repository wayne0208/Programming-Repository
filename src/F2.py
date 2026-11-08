import model

PERIODS = "123456789abc"                                  # 節次順序:1~9、a、b、c
DAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]

def find_course(courses, code):
    for c in courses:
        if c[0] == code:
            return c
    return None

def find_activity(activities, code):
    for a in activities:
        if a[0] == code:
            return a
    return None

def get_activity_slots(activity):
    if isinstance(activity[3], str):
        return [activity[3]]
    return activity[3]

def get_activity_room(activity):
    return activity[-1]

def find_student(students, student_id):
    for s in students:
        if s[0] == student_id:
            return s
    return None

def get_student_codes(student):
    codes = []
    for day in student[4]:
        for code in day:
            if code and code not in codes:          # 空格是 ""（或 None），跳過
                codes.append(code)
    return codes

def get_current_credits(student, courses):
    total = 0
    for code in get_student_codes(student):
        course = find_course(courses, code)
        if course is not None:
            total += course[2]
    return total

def find_overlap(slots1, slots2):
    overlap = []
    for s in slots1:
        if s in slots2:
            overlap.append(s)
    return overlap

def slot_key(slot):
    return (int(slot[0]), PERIODS.index(slot[2]))

def slots_text(slots):
    text = ""
    for day in range(1, 8):                               # 星期 1~7
        periods = []
        for s in sorted(slots, key=slot_key):             # 先把時段排好
            if int(s[0]) == day:
                periods.append(s[2])
        if len(periods) > 0:
            if text != "":
                text += ";"                              # 不同天用分號隔開
            text += "星期" + DAY_NAMES[day - 1] + "第 " + "、".join(periods) + " 節"
    return text

def make_conflict(overlap, detail):
    first = min(overlap, key=slot_key)
    day, period = slot_key(first)
    return (day, period, slots_text(overlap) + "\n" + detail)

def check_course_conflict(student, new_course, courses):
    conflicts = []
    for code in get_student_codes(student):
        old_course = find_course(courses, code)
        if old_course is None:
            continue
        if old_course[0] == new_course[0]:                # 已經選過同一門課
            conflicts.append((99, 0, "已經選過這門課:" + old_course[0] + " " + old_course[1]))
            continue
        overlap = find_overlap(new_course[8], old_course[8])
        if len(overlap) > 0:
            conflicts.append(make_conflict(overlap, "已選課程:" + old_course[0] + " " + old_course[1]))
    return conflicts

def check_classroom_conflict(new_course, courses, activities):
    conflicts = []
    room = new_course[7]                                  # 新課程的教室

    for c in courses:                                     # 跟所有其他課程比
        if c[0] != new_course[0] and c[7] == room:
            overlap = find_overlap(new_course[8], c[8])
            if len(overlap) > 0:
                conflicts.append(make_conflict(overlap, "教室 " + room + " 已被課程使用:" + c[0] + " " + c[1]))

    for a in activities:                                  # 跟所有活動比
        if get_activity_room(a) == room:
            overlap = find_overlap(new_course[8], get_activity_slots(a))
            if len(overlap) > 0:
                conflicts.append(make_conflict(overlap, "教室 " + room + " 已被活動使用:" + a[0] + " " + a[1]))
    return conflicts

def check_activity_conflict(student, new_course, activities):
    conflicts = []
    for code in get_student_codes(student):
        activity = find_activity(activities, code)
        if activity is None:
            continue
        overlap = find_overlap(new_course[8], get_activity_slots(activity))
        if len(overlap) > 0:
            conflicts.append(make_conflict(overlap, "已參加活動:" + activity[0] + " " + activity[1]))
    return conflicts

def check_credit_limit(student, new_course, courses):
    current = get_current_credits(student, courses)
    after = current + new_course[2]                       # 加選後學分
    if after > student[3]:
        return [(99, 1, "學分超過上限")]
    return []

def check_course_capacity_limit(new_course):
    if new_course[6] >= new_course[5]:
        return [(99, 2, "課程已額滿(" + str(new_course[6]) + "/" + str(new_course[5]) + ")")]
    return []

def check_enrollment(students, courses, activities, student_id, course_code):
    result = {"error": "", "student": student_id, "code": course_code, "name": "",
              "ok": False, "conflicts": [], "current": 0, "after": 0, "limit": 0}

    student = find_student(students, student_id)
    if student is None:
        result["error"] = "找不到這位學生"
        return result
    new_course = find_course(courses, course_code)
    if new_course is None:
        result["error"] = "找不到這門課程"
        return result

    # 五項檢查
    conflicts = []
    conflicts += check_course_conflict(student, new_course, courses)
    conflicts += check_classroom_conflict(new_course, courses, activities)
    conflicts += check_activity_conflict(student, new_course, activities)
    conflicts += check_credit_limit(student, new_course, courses)
    conflicts += check_course_capacity_limit(new_course)

    # 依星期、節次排序
    conflicts.sort(key=lambda x: (x[0], x[1]))

    current = get_current_credits(student, courses)
    result["name"] = new_course[1]
    result["ok"] = (len(conflicts) == 0)                  # 一個衝突都沒有才算成功
    result["conflicts"] = [x[2] for x in conflicts]       # 只留下說明文字
    result["current"] = current
    result["after"] = current + new_course[2]
    result["limit"] = student[3]
    return result

def print_result(result):
    if result["error"] != "":
        print("報錯拒絕,提示:" + result["error"])
        return
    print("學生:" + str(result["student"]))
    print("欲加選:" + result["code"] + " " + result["name"])
    if result["ok"]:
        print("選課結果:成功")
    else:
        print("選課結果:失敗")
    number = 1
    for text in result["conflicts"]:
        print("衝突 " + str(number) + ":" + text)
        number += 1
    print("目前學分:" + str(result["current"]))
    print("加選後學分:" + str(result["after"]))
    print("學分上限:" + str(result["limit"]))

def student_add_new_course():
    courses = model.course                                # 課程資料
    students = model.students                             # 學生資料
    activities = model.activitys                          # 活動資料
    try:
        student_id = int(input("學號:").strip())
    except ValueError:
        print("報錯拒絕,提示:學號必須是數字")
        return
    course_code = input("欲加選課程代碼:").strip()
    result = check_enrollment(students, courses, activities, student_id, course_code)
    print_result(result)


if __name__ == "__main__":
    student_add_new_course()
