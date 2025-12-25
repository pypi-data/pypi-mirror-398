"""
Location 查询引擎
从原项目迁移并适配 MCP 服务
"""

from __future__ import annotations

import os
import duckdb
from typing import Dict, Any, List


class LocationQueryEngine:
    """Location 数据查询引擎"""
    
    def __init__(self):
        # 数据文件路径 - 使用包内的数据目录
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    def query_bank_attribution(self, card_numbers: List[str]) -> List[Dict[str, Any]]:
        """查询银行卡归属地信息"""
        if not card_numbers:
            raise ValueError("银行卡号列表不能为空")
        
        if len(card_numbers) > 1000:
            raise ValueError("银行卡号列表最多支持1000个")
        
        db_path = os.path.join(self.data_dir, "bank_card_bin_data.duckdb")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"银行归属地数据库文件不存在: {db_path}")
        
        conn = duckdb.connect(db_path)
        
        try:
            # 构建查询条件
            conditions = []
            for card_num in card_numbers:
                # 提取银行卡BIN（前6位）
                bin_code = card_num[:6]
                conditions.append(f"'{bin_code}'")
            
            condition_str = ", ".join(conditions)
            
            # 执行查询
            query = f"""
            SELECT 
                卡BIN as bin_code,
                银行名称 as bank_name,
                卡类型 as card_type,
                卡号长度 as card_length
            FROM bank_card_bin 
            WHERE 卡BIN IN ({condition_str})
            """
            
            result = conn.execute(query).fetchall()
            
            # 转换为字典列表
            results = []
            for row in result:
                results.append({
                    "bin_code": row[0],
                    "bank_name": row[1],
                    "card_type": row[2],
                    "card_length": row[3]
                })
            
            return results
            
        finally:
            conn.close()
    
    def query_id_attribution(self, id_numbers: List[str]) -> List[Dict[str, Any]]:
        """查询身份证归属地信息"""
        if not id_numbers:
            raise ValueError("身份证号列表不能为空")
        
        if len(id_numbers) > 1000:
            raise ValueError("身份证号列表最多支持1000个")
        
        db_path = os.path.join(self.data_dir, "id_location.duckdb")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"身份证归属地数据库文件不存在: {db_path}")
        
        conn = duckdb.connect(db_path)
        
        try:
            # 构建查询条件
            conditions = []
            for id_num in id_numbers:
                # 提取身份证前6位地区代码
                area_code = id_num[:6]
                conditions.append(f"'{area_code}'")
            
            condition_str = ", ".join(conditions)
            
            # 执行查询
            query = f"""
            SELECT 
                代码 as area_code,
                区域 as region
            FROM id_location 
            WHERE 代码 IN ({condition_str})
            """
            
            result = conn.execute(query).fetchall()
            
            # 转换为字典列表
            results = []
            for row in result:
                results.append({
                    "area_code": row[0],
                    "region": row[1]
                })
            
            return results
            
        finally:
            conn.close()
    
    def query_ip_attribution(self, ip_addresses: List[str]) -> List[Dict[str, Any]]:
        """查询IP归属地信息"""
        if not ip_addresses:
            raise ValueError("IP地址列表不能为空")
        
        if len(ip_addresses) > 1000:
            raise ValueError("IP地址列表最多支持1000个")
        
        db_path = os.path.join(self.data_dir, "ip_location.duckdb")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"IP归属地数据库文件不存在: {db_path}")
        
        conn = duckdb.connect(db_path)
        
        try:
            import ipaddress
            
            results = []
            
            for ip in ip_addresses:
                try:
                    # 将IP地址转换为整数
                    ip_obj = ipaddress.ip_address(ip)
                    ip_int = int(ip_obj)
                    
                    # 提取IP的前两段用于初步筛选，提高查询效率
                    ip_parts = ip.split('.')
                    prefix = f"{ip_parts[0]}.{ip_parts[1]}"
                    
                    # 查询可能匹配的IP段
                    query = f"""
                    SELECT 
                        IPAddress,
                        SubnetMask,
                        MaskLength,
                        ISP,
                        Region
                    FROM ip_location 
                    WHERE IPAddress LIKE '{prefix}%'
                    """
                    
                    candidates = conn.execute(query).fetchall()
                    
                    # 遍历候选IP段，找到匹配的
                    matched = False
                    for row in candidates:
                        ip_addr, subnet_mask, mask_len, isp, region = row
                        try:
                            # 构建网络对象并判断IP是否在该网段内
                            network = ipaddress.ip_network(f"{ip_addr}/{mask_len}", strict=False)
                            if ip_obj in network:
                                results.append({
                                    "query_ip": ip,
                                    "network_address": ip_addr,
                                    "subnet_mask": subnet_mask,
                                    "mask_length": mask_len,
                                    "isp": isp,
                                    "region": region
                                })
                                matched = True
                                break
                        except:
                            continue
                    
                    # 如果前两段没找到，尝试只用第一段查询
                    if not matched:
                        query = f"""
                        SELECT 
                            IPAddress,
                            SubnetMask,
                            MaskLength,
                            ISP,
                            Region
                        FROM ip_location 
                        WHERE IPAddress LIKE '{ip_parts[0]}.%'
                        """
                        
                        candidates = conn.execute(query).fetchall()
                        
                        for row in candidates:
                            ip_addr, subnet_mask, mask_len, isp, region = row
                            try:
                                network = ipaddress.ip_network(f"{ip_addr}/{mask_len}", strict=False)
                                if ip_obj in network:
                                    results.append({
                                        "query_ip": ip,
                                        "network_address": ip_addr,
                                        "subnet_mask": subnet_mask,
                                        "mask_length": mask_len,
                                        "isp": isp,
                                        "region": region
                                    })
                                    break
                            except:
                                continue
                                
                except Exception as e:
                    # 如果某个IP查询失败，跳过继续处理其他IP
                    continue
            
            return results
            
        finally:
            conn.close()
    
    def query_mobile_attribution(self, phone_numbers: List[str]) -> List[Dict[str, Any]]:
        """查询手机号归属地信息"""
        if not phone_numbers:
            raise ValueError("手机号列表不能为空")
        
        if len(phone_numbers) > 1000:
            raise ValueError("手机号列表最多支持1000个")
        
        db_path = os.path.join(self.data_dir, "mobile_location.duckdb")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"手机号归属地数据库文件不存在: {db_path}")
        
        conn = duckdb.connect(db_path)
        
        try:
            # 构建查询条件
            conditions = []
            for phone in phone_numbers:
                # 提取手机号前7位（匹配mobile字段）
                mobile_prefix = phone[:7]
                conditions.append(f"'{mobile_prefix}'")
            
            condition_str = ", ".join(conditions)
            
            # 执行查询
            query = f"""
            SELECT 
                prefix,
                province,
                city,
                isp,
                code as area_code,
                zip as zip_code
            FROM mobile_location 
            WHERE mobile IN ({condition_str})
            """
            
            result = conn.execute(query).fetchall()
            
            # 转换为字典列表
            results = []
            for row in result:
                results.append({
                    "prefix": row[0],
                    "province": row[1],
                    "city": row[2],
                    "isp": row[3],
                    "area_code": row[4],
                    "zip_code": row[5]
                })
            
            return results
            
        finally:
            conn.close()
