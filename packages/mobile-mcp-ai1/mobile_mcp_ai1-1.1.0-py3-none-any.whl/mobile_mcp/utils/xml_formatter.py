#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML格式化器 - 将XML元素格式化成AI可理解的格式

功能：
1. 将XML元素列表格式化成类似Web accessibility tree的格式
2. 提取关键信息供AI分析
3. 优化格式以提高AI理解准确率
"""
from typing import List, Dict


class XMLFormatter:
    """
    XML格式化器
    
    用法:
        formatter = XMLFormatter()
        formatted = formatter.format(elements)
    """
    
    def format(self, elements: List[Dict]) -> str:
        """
        格式化元素列表
        
        Args:
            elements: 元素列表（来自XMLParser）
            
        Returns:
            格式化后的字符串（AI可理解的格式）
        """
        formatted_lines = []
        
        for element in elements:
            line = self._format_element(element)
            if line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_element(self, element: Dict) -> str:
        """
        格式化单个元素
        
        Args:
            element: 元素字典
            
        Returns:
            格式化后的字符串
        """
        # 获取元素类型（简化类名）
        class_name = element.get('class_name', 'element')
        if not class_name:
            class_name = 'element'
        
        # 转换为更友好的名称
        type_mapping = {
            'Button': 'button',
            'TextView': 'text',
            'EditText': 'textbox',
            'ImageView': 'image',
            'LinearLayout': 'container',
            'RelativeLayout': 'container',
            'FrameLayout': 'container',
            'RecyclerView': 'list',
            'ScrollView': 'scrollable',
        }
        
        element_type = type_mapping.get(class_name, class_name.lower())
        
        # 构建格式化字符串
        parts = [element_type]
        
        # 添加文本内容
        text = element.get('text', '').strip()
        if text:
            # 限制文本长度
            if len(text) > 50:
                text = text[:47] + '...'
            parts.append(f'"{text}"')
        
        # 添加resource-id（最重要）
        resource_id = element.get('resource_id', '')
        if resource_id:
            parts.append(f'(resource-id: {resource_id})')
        
        # 添加content-desc（无障碍描述）
        content_desc = element.get('content_desc', '')
        if content_desc and content_desc != text:
            parts.append(f'(description: {content_desc})')
        
        # 添加可交互状态
        if element.get('clickable'):
            parts.append('[clickable]')
        if element.get('focusable'):
            parts.append('[focusable]')
        
        # 添加bounds（坐标信息，可选）
        bounds = element.get('bounds', '')
        if bounds and not resource_id:  # 如果没有resource-id，提供坐标作为备选
            parts.append(f'(bounds: {bounds})')
        
        return ' '.join(parts)
    
    def format_for_ai(self, elements: List[Dict], query: str = "") -> str:
        """
        为AI分析优化的格式化
        
        Args:
            elements: 元素列表
            query: 用户查询（用于过滤相关元素）
            
        Returns:
            优化后的格式化字符串
        """
        # 如果有关键词，优先显示相关元素
        if query:
            query_lower = query.lower()
            relevant_elements = []
            other_elements = []
            
            for element in elements:
                text = element.get('text', '').lower()
                resource_id = element.get('resource_id', '').lower()
                content_desc = element.get('content_desc', '').lower()
                
                if (query_lower in text or 
                    query_lower in resource_id or 
                    query_lower in content_desc):
                    relevant_elements.append(element)
                else:
                    other_elements.append(element)
            
            # 相关元素在前
            sorted_elements = relevant_elements + other_elements
        else:
            sorted_elements = elements
        
        # 限制元素数量（避免AI token过多）
        max_elements = 100
        if len(sorted_elements) > max_elements:
            sorted_elements = sorted_elements[:max_elements]
        
        return self.format(sorted_elements)

