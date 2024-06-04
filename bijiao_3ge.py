from read_data import *
from docplex.cp.model import *
import docplex
import time


exponent_k = 0.5
# POI_number = 50





from collections import namedtuple

# 写个小例子
# (values, times)


# cplex求解最优
def cp_opt_alloc():

    start_time = time.time()
    # 创建模型
    model = CpoModel()

    this_luan_users = luanxu[:users_number]
    print(this_luan_users)

    this_poi_luan = daluan_poi[:POI_number]

    # 定义决策变量
    x_vars = {i: model.binary_var(name="x_{0}".format(i)) for i in this_luan_users}
    # x_vars

    # 添加约束条件
    model.add(model.sum(x_vars[i] * user_data_set[i].cost for i in this_luan_users) <= Budget)

    # 定义目标函数
    # objective = model.sum(POI_fina_set[j].values * docplex.cp.modeler.power(
    #     model.min(model.sum(x_vars[i] * user_data_set[i].POI_select[j] for i in this_luan_users),
    #               POI_fina_set[j].times)/POI_fina_set[j].times, exponent_k) for j in range(len(POI_fina_set)))

    # 定义目标函数（以POI点个数探究）
    objective = model.sum(POI_fina_set[j].values * docplex.cp.modeler.power(
        model.min(model.sum(x_vars[i] * user_data_set[i].POI_select[j] for i in this_luan_users),
                  POI_fina_set[j].times) / POI_fina_set[j].times, exponent_k) for j in this_poi_luan)

    # 最大化目标：
    model.add(model.maximize(objective))

    # 求解模型
    sol = model.solve(TimeLimit=600)
    end_time = time.time()
    execution_time = end_time - start_time

    # 得到模型的集合
    solution_vector = []
    for i in this_luan_users:
        solution_vector.append(sol[x_vars[i]])

    solution_set = []
    for j in range(users_number):
        if solution_vector[j] != 0:
            solution_set.append(this_luan_users[j])


    return solution_set, execution_time


# 看给定集合使用的预算
def Budget_of_use_opt(select_user_list):
    sum_Budget = 0
    for i in select_user_list:
        sum_Budget += user_data_set[i].cost
    return sum_Budget


# 价值函数
# def value_fun(user_list):
#
#     if len(user_list) == 0:
#         return 0
#
#     total_values = 0
#     # user_list是选中用户的下标的列表
#     for poi in range(POI_number):
#         # 单个POI点的价值
#         sum_users = 0
#         for i in range(len(user_list)):
#             # 计算参与点poi的用户数
#             sum_users = user_data_set[user_list[i]].POI_select[poi] + sum_users
#
#         min_times = min(sum_users, POI_fina_set[poi].times)
#         # print("POI点:", poi, "     有效参与人数为：", min_times)
#         # print(POI_fina_set[poi].values, " * " * 5, min_times, " * " * 5, POI_fina_set[poi].times)
#         single_value = POI_fina_set[poi].values * (min_times / POI_fina_set[poi].times) ** exponent_k
#         # print("单个POI点：", poi, "的价值为：", single_value)
#
#         total_values = total_values + single_value
#
#     return total_values

# 下面是时钟算法
def value_fun(user_list):

    # print("此时value_fun函数中POI_number为：", POI_number)

    if len(user_list) == 0:
        return 0

    total_values = 0
    # user_list是选中用户的下标的列表
    for poi in range(POI_number):
        # 单个POI点的价值
        sum_users = 0
        for i in range(len(user_list)):
            # 计算参与点poi的用户数
            sum_users = user_data_set[user_list[i]].POI_select[daluan_poi[poi]] + sum_users

        min_times = min(sum_users, POI_fina_set[daluan_poi[poi]].times)
        # print("POI点:", poi, "     有效参与人数为：", min_times)
        # print(POI_fina_set[poi].values, " * " * 5, min_times, " * " * 5, POI_fina_set[poi].times)
        single_value = POI_fina_set[daluan_poi[poi]].values * (min_times / POI_fina_set[daluan_poi[poi]].times) ** exponent_k
        # print("单个POI点：", poi, "的价值为：", single_value)

        total_values = total_values + single_value

    return total_values

# 找到边际价值最大的用户函数
def find_most_marginal_value_user(select_user_list, the_rest_user_list):

    if len(the_rest_user_list) == 0:
        return -1

    max_value = 0
    argmax = -1
    for i in the_rest_user_list:
        s_u_l_fu = select_user_list.copy()
        s_u_l_fu.append(i)
        if value_fun(s_u_l_fu) > max_value:
            argmax = i
    return argmax

# 集合相减函数
def set_sub(list1, list2):
    result = [item for item in list1 if item not in list2]
    return result

# 用户对集合S产生的边际价值
def user_marginal_value(select_u_list, user_i):
    userrr = select_u_list.copy()
    userrr.append(user_i)
    return value_fun(userrr) - value_fun(select_u_list)
# user_data_set
# 时钟拍卖算法：
def clock_al():

    start_time = time.time()

    # 初始化
    active_user_set = luanxu[:users_number]
    # print(active_user_set)

    set_total = [[], []]
    set_total[1].append(find_most_marginal_value_user([], active_user_set))

    OPT_i = value_fun(set_total[1])
    # print("这个就是OPT：", OPT_i)
    # 轮次t
    t = 1

    price_set = [Budget] * len(user_data_set)

    while (len(active_user_set) - len(set_total[0]) - len(set_total[1])) != 0:
        t += 1

        # 最大值翻倍
        OPT_i = 2 * OPT_i
        # print("这个就是OPT：", OPT_i)

        if t % 2 == 0:
            now_set = 0
        else:
            now_set = 1

        set_total[now_set].clear()
        while value_fun(set_total[now_set]) < OPT_i and len(active_user_set)-len(set_total[0])-len(set_total[1]) != 0:

            # print("判断条件为什么没有生效", value_fun(set_total[now_set]) < OPT_i)
            most_mar_val_user = find_most_marginal_value_user(set_total[now_set], set_sub(active_user_set, set_total[0] + set_total[1]))

            price_set[most_mar_val_user] = min(price_set[most_mar_val_user],
                                               user_marginal_value(set_total[now_set], most_mar_val_user) * (
                                                           Budget / OPT_i))

            # 如果给的价格用户接受，就在active_user_set里面留下用户，反之踢出
            if price_set[most_mar_val_user] > user_data_set[most_mar_val_user].cost:
                set_total[now_set].append(most_mar_val_user)
            else:
                active_user_set.remove(most_mar_val_user)


    # 计算用户集合的价格
    def price_of_user_set(user_list):
        price_sum = 0
        for u in user_list:
            price_sum += price_set[u]
        return price_sum

    # 找到在list_2中对list_1 边际价值/价格  最大的用户
    def find_most_mar_price_user(list_1, list_2):

        if len(list_2) == 0:
            return -1

        return_user = -1
        most_mar_price = 0
        for u in list_2:
            # test_ii = user_marginal_value(list_1, u)
            # test_i2 = price_set[u]
            # test_i3 = test_ii/test_i2
            # print("这个是手动阀手动阀：", test_ii, test_i2, test_i3)
            if (user_marginal_value(list_1, u) / price_set[u]) > most_mar_price:
                return_user = u

        return return_user

    # print("sdfazsdfasd" * 20)
    # print(set_total[0])
    # print(set_total[1])


    # 拍卖过程结束，会得到两个集合
    # Win_set1是算法中的W1
    # Win_set2是算法中的W—2
    if t % 2 == 0:
        Win_set1 = set_total[1]
        Win_set2 = set_total[0]
    else:
        Win_set1 = set_total[0]
        Win_set2 = set_total[1]
    if value_fun(Win_set2) > OPT_i:
        Win_set2.pop()

    set_1_copy = Win_set1.copy()
    while len(set_1_copy) != 0:

        # 贪婪的找到用户
        find_user_1 = find_most_mar_price_user(Win_set2, set_1_copy)
        # set_1_copy.remove(find_user_1)

        # 判断用户加入是否会超出预算
        # 先判断找到的用户是否不为-1
        if find_user_1 == -1:
            break
        else:
            set_1_copy.remove(find_user_1)
            if price_of_user_set(Win_set2) + price_set[find_user_1] <= Budget:
                Win_set2.append(find_user_1)


    end_time = time.time()
    execution_time = end_time - start_time

    return Win_set2, price_of_user_set(Win_set2), execution_time


# 找到对select_user_list集合（边际价值/报价）最大的用户函数：即arg maxj∈UVj|A bj
def find_user_of_most_marvalue_bid(select_user_list, the_rest_user_list):

    initial_mar_v = 0
    final_select_user = -1
    for i in the_rest_user_list:

        # 用户i产生的边际价值为：
        u_find_mar_v = user_marginal_value(select_user_list, i)
        # 用户i的报价为:这里用真实成本cost，后面可以改
        u_find_bid = user_data_set[i].cost
        if u_find_bid == 0:
            continue
        # 用户i的边际/bid为:
        u_mar_bid = u_find_mar_v / u_find_bid
        # print("用户", i, "的边际价值为：", u_find_mar_v, "   报价为：", u_find_bid, "  边际/bid为：", u_mar_bid)

        # 确定i是不是当前的最大
        if u_mar_bid > initial_mar_v:
            # 说明此时i是目前最大的
            final_select_user = i
            initial_mar_v = u_mar_bid




    # 当遍历完一遍后找到了最大的, 当final_select_user = -1时说明u_find_mar_v=0，即剩余用户不会产生边际价值了

    return final_select_user




# 下面是真实贪婪算法
def SM_all_pay_M():

    # print("此时的POI个数为：", POI_number)
    print("此时用户数为：", len(luanxu[:users_number]))

    print("此时预算为：", Budget)

    start_time = time.time()

    all_users_copy = luanxu[:users_number]
    # print(all_users_copy)
    # 算法的第一行：
    set_A = []
    user_i = find_user_of_most_marvalue_bid(set_A, all_users_copy)
    # print(user_i)


    # 算法2-3行
    while user_data_set[user_i].cost <= Budget * (user_marginal_value(set_A, user_i) / value_fun(set_A + [user_i])):
        set_A.append(user_i)
        all_users_copy.remove(user_i)
        user_i = find_user_of_most_marvalue_bid(set_A, all_users_copy)
        if user_i == -1:
            break

    # 算法5-6行
    price_set = [0] * len(user_data_set)

    # 上面已经找到了集合A
    # print("找到的set_A为：", set_A)

    # 算法8行开始
    for u in set_A:

        # 为每个A里面的u找一个备胎，用来确定给u的价格
        # 下面时算法第9行
        all_users_copy_2 = luanxu[:users_number]
        # print("*" * 60)
        # print("下面是第一个all_users_copy_2")
        # print(all_users_copy_2)
        all_users_copy_2.remove(u)

        set_A_ = []

        user_u = find_user_of_most_marvalue_bid(set_A_, all_users_copy_2)
        # print(user_i)

        # 算法2-3行
        while user_data_set[user_u].cost <= Budget * (user_marginal_value(set_A_, user_u) / value_fun(set_A_ + [user_u])):
            # print("下面是set_A_")
            # print(set_A_)
            # print("下面是all_users_copy_2")

            set_A_.append(user_u)
            all_users_copy_2.remove(user_u)
            user_u = find_user_of_most_marvalue_bid(set_A_, all_users_copy_2)
            if user_u == -1:
                break

        # 得到了A_(当没有u的赢家集合set_A_)
        # print("当没有",u,"时获胜的用户集合为：",set_A_)
        # 找出set_A_中与set_A不同的元素
        different_elements = [item for item in set_A_ if item not in set_A]
        if len(different_elements) == 0:
            price_set[u] = 0
        else:
            # 找到这个替代用户
            u_alternative = different_elements[0]
            # 确定这个用户在set_A_中的位置
            u_alternative_position = set_A_.index(u_alternative)
            # 找到u在set_A中的位置
            u_position = set_A.index(u)

            # 得到u对选中他时的边际价值
            u_V = user_marginal_value(set_A[:u_position], u)

            # 得到u_alternative对选中他时的边际价值
            u_alternative_V = user_marginal_value(set_A_[:u_alternative_position], u_alternative)

            price_set[u] = u_V * user_data_set[u_alternative].cost / u_alternative_V


        del all_users_copy_2

    final_win_set = set_A.copy()
    for i in set_A:
        if price_set[i] == 0:
            final_win_set.remove(i)



    end_time = time.time()
    execution_time = end_time - start_time



    return final_win_set, price_set, execution_time







cl_result = []
cl_cost = []
cl_u_number = []
cl_time = []
SM_result = []
SM_cost = []
SM_u_number = []
SM_time = []
op_result = []
op_cost = []
op_u_number = []
op_time = []




# 修改下面的值来看比较
users_number = 200
Budget = 400
# POI_number = 50

# 此时是比较POI数量变化的情况
for POI_number in range(10, 51, 10):
    al_set, fina_had_used_budget, used_time_1 = clock_al()
    # print(al_set)
    cl_result.append(value_fun(al_set))
    cl_cost.append(fina_had_used_budget)
    cl_u_number.append(len(al_set))
    cl_time.append(used_time_1)

    win_set, price, used_time_2 = SM_all_pay_M()
    SM_result.append(value_fun(win_set))
    SM_cost.append(sum(price))
    SM_u_number.append(len(win_set))
    SM_time.append(used_time_2)

    sol_set, ex_times = cp_opt_alloc()
    op_result.append(value_fun(sol_set))
    op_cost.append(Budget_of_use_opt(sol_set))
    op_u_number.append(len(sol_set))
    op_time.append(ex_times)



print("时钟拍卖的结果为：")
print("价值：", cl_result)
print("成本：", cl_cost)
print("获胜人数：", cl_u_number)
print("使用时间：", cl_time)

print("*" * 50)

print("SM的结果为：")
print("价值：", SM_result)
print("成本：", SM_cost)
print("获胜人数：", SM_u_number)
print("使用时间：", SM_time)

print("*" * 50)

print("OPT的结果为：")
print("价值：", op_result)
print("成本：", op_cost)
print("获胜人数：", op_u_number)
print("使用时间：", op_time)