## 介绍
一个解析 ini 文件的库

## 特性
1. API 简洁性: 属性 / 字典双模式访问  
1.1 属性访问模式  
1.2 字典访问模式  
1.3 混合访问模式  
1.4 支持 in 操作符  
2. 异常处理  
2.1 使用异常策略（默认）  
2.2 使用结果策略  
2.3 使用静默策略  

## 环境配置
1. 系统: Linux/Windows
2. 语言: Python 3.9+
3. 依赖安装: pip install etiniconf

## 使用样例:
1. INI文件 config.ini
```
[server]
host = 192.168.0.10
port = 22
```
2. 使用样例
```
import etiniconf

def main(filepath):
    """
    异常策略（默认）:
    conf = etiniconf.ConfiniParserFactory.create_with_exception_strategy(filepath)
    结果策略:
    conf = etiniconf.ConfiniParserFactory.create_with_result_strategy(filepath)  
    静默策略:
    conf = etiniconf.ConfiniParserFactory.create_with_silent_strategy(filepath)
    """
    # 使用静默策略
    conf = etiniconf.ConfiniParserFactory.create_with_silent_strategy(filepath)   

    # 1. 属性访问模式    
    try:
        host = conf.server.host
        port = conf.server.port
        print(f"host={host}, port={port}")
    except AttributeError as e:
        print(f"Error: {e}")
    
    # 2. 字典访问模式
    try:
        host = conf['server']['host']
        port = conf['server']['port']
        print(f"host={host}, port={port}")
    except etiniconf.ConfiniError as e:
        print(f"Error: {e}")
    
    # 3. 混合访问模式
    try:
        host = conf.server['host']
        port = conf['server'].port
        print(f"host={host}, port={port}")
    except (AttributeError, etiniconf.ConfiniError) as e:
        print(f"Error: {e}")
    
    # 4. 支持 in 操作符
    section = 'server1'
    if section in conf:
        print(f"The {section} does exist")
    else:
        print(f"The {section} does not exist")

if __name__ == '__main__':
    f = 'config.ini'
    main(f)
```
