def euler_method(f, y0, t_range, n):
    """
    Решение ОДУ первого порядка: y' = f(t, y)
    методом Эйлера.
    
    Parameters:
    -----------
    f : function
        Функция правой части уравнения: f(t, y)
    y0 : float
        Начальное значение y(t0)
    t_range : tuple
        Интервал (t0, t_end)
    n : int
        Количество шагов
    
    Returns:
    --------
    tuple: (t_values, y_values)
    """
    t0, t_end = t_range
    h = (t_end - t0) / n  # шаг
    
    t_values = [t0]
    y_values = [y0]
    
    t = t0
    y = y0
    
    for _ in range(n):
        y = y + h * f(t, y)
        t = t + h
        
        t_values.append(t)
        y_values.append(y)
    
    return t_values, y_values

def second_order_to_system(f, y0, dy0, t_range, n):
    """
    Решение ОДУ второго порядка: y'' = f(t, y, y')
    путём сведения к системе двух уравнений первого порядка.
    
    Parameters:
    -----------
    f : function
        Функция правой части: f(t, y, v) где v = y'
    y0 : float
        Начальное значение y(t0)
    dy0 : float
        Начальное значение y'(t0)
    t_range : tuple
        Интервал (t0, t_end)
    n : int
        Количество шагов
    
    Returns:
    --------
    tuple: (t_values, y_values, v_values)
    """
    t0, t_end = t_range
    h = (t_end - t0) / n  # шаг
    
    # Начальные условия
    t = t0
    y = y0
    v = dy0  # v = y'
    
    t_values = [t]
    y_values = [y]
    v_values = [v]
    
    for _ in range(n):
        # Метод Эйлера для системы:
        # y' = v
        # v' = f(t, y, v)
        y_new = y + h * v
        v_new = v + h * f(t, y, v)
        
        t = t + h
        
        t_values.append(t)
        y_values.append(y_new)
        v_values.append(v_new)
        
        y, v = y_new, v_new
    
    return t_values, y_values, v_values