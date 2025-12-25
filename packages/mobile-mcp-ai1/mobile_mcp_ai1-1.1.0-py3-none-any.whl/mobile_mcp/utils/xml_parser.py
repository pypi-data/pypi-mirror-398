#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML解析器 - 解析UIAutomator2的XML结构

功能：
1. 解析XML格式的页面结构
2. 提取元素属性（text, resource-id, class, bounds等）
3. 构建元素树结构
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import re


class XMLParser:
    """
    XML解析器
    
    用法:
        parser = XMLParser()
        elements = parser.parse(xml_string)
    """
    
    def parse(self, xml_string: str) -> List[Dict]:
        """
        解析XML字符串
        
        Args:
            xml_string: XML格式的字符串
            
        Returns:
            元素列表，每个元素包含属性信息
        """
        try:
            # 确保xml_string是字符串类型
            if not isinstance(xml_string, str):
                xml_string = str(xml_string)
            
            # 如果xml_string为空或无效，返回空列表
            if not xml_string or not xml_string.strip():
                return []
            
            root = ET.fromstring(xml_string)
            elements = []
            self._parse_node(root, elements, depth=0)
            return elements
        except ET.ParseError as e:
            raise ValueError(f"XML解析失败: {e}")
        except Exception as e:
            raise ValueError(f"XML解析异常: {e}, xml_string类型: {type(xml_string)}, 前100字符: {str(xml_string)[:100]}")
    
    def _parse_node(self, node: ET.Element, elements: List[Dict], depth: int = 0):
        """
        递归解析节点
        
        Args:
            node: XML节点
            elements: 元素列表（输出）
            depth: 当前深度
        """
        # 提取节点属性
        element = {
            'text': node.get('text', ''),
            'resource_id': node.get('resource-id', ''),
            'class': node.get('class', ''),
            'content_desc': node.get('content-desc', ''),
            'bounds': node.get('bounds', ''),
            'clickable': node.get('clickable', 'false') == 'true',
            'focusable': node.get('focusable', 'false') == 'true',
            'scrollable': node.get('scrollable', 'false') == 'true',
            'enabled': node.get('enabled', 'true') == 'true',
            'depth': depth,
        }
        
        # 解析bounds坐标
        if element['bounds']:
            bounds = self._parse_bounds(element['bounds'])
            element['x'] = bounds.get('x', 0)
            element['y'] = bounds.get('y', 0)
            element['width'] = bounds.get('width', 0)
            element['height'] = bounds.get('height', 0)
        
        # 提取类名（简化）
        if element['class']:
            class_parts = element['class'].split('.')
            element['class_name'] = class_parts[-1] if class_parts else ''
        else:
            element['class_name'] = ''
        
        # 只添加有意义的元素（有文本、resource-id或可交互）
        if (element['text'] or 
            element['resource_id'] or 
            element['clickable'] or 
            element['focusable']):
            elements.append(element)
        
        # 递归处理子节点
        for child in node:
            self._parse_node(child, elements, depth + 1)
    
    def _parse_bounds(self, bounds_str: str) -> Dict:
        """
        解析bounds字符串
        
        Args:
            bounds_str: 格式如 "[100,200][300,400]"
            
        Returns:
            包含x, y, width, height的字典
        """
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return {
                'x': x1,
                'y': y1,
                'width': x2 - x1,
                'height': y2 - y1,
            }
        return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

