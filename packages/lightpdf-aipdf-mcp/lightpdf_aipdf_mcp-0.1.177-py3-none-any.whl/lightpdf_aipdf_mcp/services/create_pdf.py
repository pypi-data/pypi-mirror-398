"""根据用户输入请求创建PDF文件的接口"""
from dataclasses import dataclass
from typing import Optional
import os
import uuid
import httpx
from ..utils.common import Logger, FileHandler, BaseResult, BaseApiClient, require_api_key
from .converter import Converter, ConversionResult

@dataclass
class CreatePdfResult(BaseResult):
    """文档创建结果数据类（支持PDF/Word/Excel等格式）"""
    pass

class DocumentCreator(BaseApiClient):
    """通用文档创建器（支持PDF/Word/Excel等格式）"""
    def __init__(self, logger: Logger, file_handler: FileHandler):
        super().__init__(logger, file_handler)
        self.api_base_url = f"https://{self.api_endpoint}/tasks/llm/chats"
        # 语言代码到语言名称的映射
        # 语言代码到英文全称的映射（与前端 languageConfig 的 value 对应）
        self.language_map = {
            "zh": "Simplified Chinese",
            "en": "English",
            "de": "German",
            "es": "Spanish",
            "fr": "French",
            "jp": "Japanese",
            "pt": "Portuguese",
            "tw": "Traditional Chinese",
            "ar": "Arabic",
            "cz": "Czech",
            "dk": "Danish",
            "fi": "Finnish",
            "gr": "Greek",
            "hu": "Hungarian",
            "it": "Italian",
            "nl": "Dutch",
            "no": "Norwegian",
            "pl": "Polish",
            "se": "Swedish",
            "tr": "Turkish"
        }

    @require_api_key
    async def create_document_from_prompt(
        self, 
        prompt: str, 
        language: str,
        provider: str,
        format_name: str,
        enable_web_search: bool = False,
        use_advanced_model: bool = False,
        original_name: Optional[str] = None
    ) -> CreatePdfResult:
        """
        根据用户输入请求创建文档。

        参数：
            prompt (str): 用户的输入请求或提示词，仅支持文字描述，不支持文件附件等。
            language (str): 生成文档的语言，必需参数。
            provider (str): 转换provider参数
            format_name (str): 格式名称，用于错误信息
            enable_web_search (bool): 是否启用联网搜索，默认False。
            use_advanced_model (bool): 是否使用高级模型，默认False。
            original_name (Optional[str]): 可选，原始文件名。
        返回：
            CreatePdfResult: 包含生成结果的信息。
        """
        tex_path = None
        try:
            # 1. 根据prompt生成latex代码
            latex_code = await self._generate_latex_code(prompt, language, enable_web_search, provider, use_advanced_model)
            if not latex_code:
                return CreatePdfResult(
                    success=False,
                    file_path="",
                    error_message="生成的latex代码为空",
                    original_name=original_name
                )

            # 2. 保存latex_code为本地.tex文件
            tex_path = await self._save_latex_to_file(latex_code)

            # 3. 调用Converter.convert_file将TEX转换为指定格式
            result = await self._convert_tex_to_format(tex_path, provider, original_name)
            
            # 转换ConversionResult到CreatePdfResult
            return CreatePdfResult(
                success=result.success,
                file_path=result.file_path,
                error_message=result.error_message,
                download_url=result.download_url,
                original_name=result.original_name,
                task_id=result.task_id
            )

        except Exception as e:
            return CreatePdfResult(
                success=False,
                file_path="",
                error_message=f"{format_name}文档创建过程中发生错误: {e}",
                original_name=original_name
            )
        finally:
            # 清理临时文件
            if tex_path and os.path.exists(tex_path):
                self._schedule_file_cleanup(tex_path)

    @require_api_key
    async def create_pdf_from_prompt(
        self, 
        prompt: str, 
        language: str,
        enable_web_search: bool = False,
        use_advanced_model: bool = False,
        original_name: Optional[str] = None
    ) -> CreatePdfResult:
        """根据用户输入请求创建PDF文件。"""
        return await self.create_document_from_prompt(
            prompt, language, "", "PDF", enable_web_search, use_advanced_model, original_name
        )

    @require_api_key
    async def create_word_from_prompt(
        self, 
        prompt: str, 
        language: str,
        enable_web_search: bool = False,
        use_advanced_model: bool = False,
        original_name: Optional[str] = None
    ) -> CreatePdfResult:
        """根据用户输入请求创建Word文档。"""
        return await self.create_document_from_prompt(
            prompt, language, "word", "Word", enable_web_search, use_advanced_model, original_name
        )

    @require_api_key
    async def create_excel_from_prompt(
        self, 
        prompt: str, 
        language: str,
        enable_web_search: bool = False,
        use_advanced_model: bool = False,
        original_name: Optional[str] = None
    ) -> CreatePdfResult:
        """根据用户输入请求创建Excel文档。"""
        return await self.create_document_from_prompt(
            prompt, language, "excel", "Excel", enable_web_search, use_advanced_model, original_name
        )

    # Template IDs 配置
    # PDF/Word 普通模型
    TEMPLATE_ID_STANDARD = "48a62054-9cf0-483d-9787-b31afc32e079"
    # PDF/Word 高级模型
    TEMPLATE_ID_ADVANCED = "9b5ab815-83ef-4110-86ad-e738176d75b3"
    # Excel 普通模型
    TEMPLATE_ID_EXCEL_STANDARD = "7fa7b5e9-9d2f-454e-bbe4-2a6f0d8893ee"
    # Excel 高级模型
    TEMPLATE_ID_EXCEL_ADVANCED = "7fa7b5e9-9d2f-454e-bbe4-2a6f0d8893ee"  # TODO: 替换为高级模型的 template_id

    async def _generate_latex_code(self, prompt: str, language: str, enable_web_search: bool, provider: str = "", use_advanced_model: bool = False) -> str:
        """根据用户输入生成LaTeX代码"""
        lang_str = self.language_map.get(language)
        await self.logger.log("debug", f"开始为语言 {lang_str} 生成LaTeX代码，联网搜索: {enable_web_search}，文档类型: {provider}，高级模型: {use_advanced_model}")
        
        # 根据文档类型和模型级别选择template_id
        if provider == "excel":
            template_id = self.TEMPLATE_ID_EXCEL_ADVANCED if use_advanced_model else self.TEMPLATE_ID_EXCEL_STANDARD
        else:
            template_id = self.TEMPLATE_ID_ADVANCED if use_advanced_model else self.TEMPLATE_ID_STANDARD
        
        # 这里应该是实际的代码生成逻辑
        # 暂时返回空字符串，需要后续实现
        async with httpx.AsyncClient(timeout=3600.0) as client:
            template_variables = {
                "PROMPT": prompt
            }
            if lang_str:
                template_variables["LANGUAGE"] = lang_str

            headers = {"X-API-KEY": self.api_key}
            data = {
                "po": "lightpdf",
                "response_type": 0,
                "template_id": template_id,
                "template_variables": template_variables
            }
            if enable_web_search:
                # 获取真实的用户信息
                plugin_options = await self._get_real_user_info(language)
                data["plugins"] = [
                    {
                        "function": {
                            "id": 1001,
                            "options": plugin_options
                        },
                        "callback": None
                    }
                ]

            await self.logger.log("debug", f"正在提交生成LaTeX代码...{data}")
            response = await client.post(self.api_base_url, json=data, headers=headers)

            task_id = await self._handle_api_response(response, "生成LaTeX代码")
            await self.logger.log("debug", f"生成LaTeX代码，task_id: {task_id}")

            return await self._wait_for_task(client, task_id, "生成LaTeX代码", result_field="text")

    async def _save_latex_to_file(self, latex_code: str) -> str:
        """保存LaTeX代码到临时文件"""
        temp_dir = "./tmp"
        os.makedirs(temp_dir, exist_ok=True)
        tex_filename = f"latex_code_{uuid.uuid4().hex}.tex"
        tex_path = os.path.join(temp_dir, tex_filename)
        
        # 清理markdown代码块标记
        cleaned_code = self._clean_latex_code(latex_code)
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
        
        return tex_path

    def _clean_latex_code(self, latex_code: str) -> str:
        """清理LaTeX代码中的markdown标记"""
        if not latex_code:
            return latex_code
        
        # 去除首行和尾行的markdown代码块标记
        lines = latex_code.strip().split('\n')
        
        # 检查并移除首行的```latex标记
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        
        # 检查并移除尾行的```标记
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        
        # 重新组合代码
        cleaned_code = '\n'.join(lines)
        
        return cleaned_code.strip()

    async def _get_real_user_info(self, language: str) -> dict:
        """获取真实的用户信息"""
        import platform
        
        # 获取真实的用户代理字符串
        system = platform.system()
        version = platform.version()
        architecture = platform.machine()
        
        # 构建更真实的User-Agent
        if system == "Darwin":  # macOS
            user_agent = f"Mozilla/5.0 (Macintosh; Intel Mac OS X {version.replace('.', '_')}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        elif system == "Windows":
            user_agent = f"Mozilla/5.0 (Windows NT {version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        elif system == "Linux":
            user_agent = f"Mozilla/5.0 (X11; Linux {architecture}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # 获取真实的IP地址
        local_ip = self._get_local_ip()
        
        # 根据语言参数动态生成accept_language
        accept_language = self._get_accept_language(language)
        
        return {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "ip": local_ip
        }

    def _get_accept_language(self, language: str) -> str:
        """根据语言代码生成对应的accept_language字符串"""
        # 语言代码到HTTP Accept-Language的映射
        language_codes = {
            "zh": "zh-CN,zh;q=0.9,en;q=0.8",
            "en": "en-US,en;q=0.9",
            "de": "de-DE,de;q=0.9,en;q=0.8",
            "es": "es-ES,es;q=0.9,en;q=0.8",
            "fr": "fr-FR,fr;q=0.9,en;q=0.8",
            "ja": "ja-JP,ja;q=0.9,en;q=0.8",
            "pt": "pt-PT,pt;q=0.9,en;q=0.8",
            "zh-tw": "zh-TW,zh;q=0.9,en;q=0.8",
            "ar": "ar-SA,ar;q=0.9,en;q=0.8",
            "cs": "cs-CZ,cs;q=0.9,en;q=0.8",
            "da": "da-DK,da;q=0.9,en;q=0.8",
            "fi": "fi-FI,fi;q=0.9,en;q=0.8",
            "el": "el-GR,el;q=0.9,en;q=0.8",
            "hu": "hu-HU,hu;q=0.9,en;q=0.8",
            "it": "it-IT,it;q=0.9,en;q=0.8",
            "nl": "nl-NL,nl;q=0.9,en;q=0.8",
            "no": "no-NO,no;q=0.9,en;q=0.8",
            "pl": "pl-PL,pl;q=0.9,en;q=0.8",
            "sv": "sv-SE,sv;q=0.9,en;q=0.8",
            "tr": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        
        return language_codes.get(language, "en-US,en;q=0.9")

    def _get_local_ip(self) -> str:
        """获取本地IP地址的稳定方法，优先获取物理网络接口IP"""
        import socket
        
        # 收集所有可能的IP地址
        candidate_ips = []
        
        # 方法1: 尝试连接外部DNS服务器
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # 使用多个DNS服务器进行尝试
                for dns_server in ["8.8.8.8", "1.1.1.1", "208.67.222.222", "114.114.114.114", "101.101.101.101", "1.2.4.8"]:
                    try:
                        s.connect((dns_server, 80))
                        ip = s.getsockname()[0]
                        if self._is_valid_local_ip(ip):
                            candidate_ips.append(ip)
                            break  # 找到第一个有效IP就停止
                    except Exception:
                        continue
        except Exception:
            pass
        
        # 方法2: 获取本机所有网络接口
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if self._is_valid_local_ip(ip) and ip not in candidate_ips:
                    candidate_ips.append(ip)
        except Exception:
            pass
        
        # 方法3: 使用系统网络接口信息
        try:
            import platform
            if platform.system() != "Windows":
                # Unix/Linux/macOS系统：尝试使用更详细的网络接口信息
                import subprocess
                result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'src' in line:
                            parts = line.split()
                            if 'src' in parts:
                                src_index = parts.index('src')
                                if src_index + 1 < len(parts):
                                    ip = parts[src_index + 1]
                                    if self._is_valid_local_ip(ip) and ip not in candidate_ips:
                                        candidate_ips.append(ip)
                                        break
        except Exception:
            pass
        
        # 选择最优IP地址
        if candidate_ips:
            return self._select_best_ip(candidate_ips)
        
        # 最后的后备方案
        return "127.0.0.1"
    
    def _select_best_ip(self, candidate_ips: list) -> str:
        """从候选IP中选择最佳的IP地址"""
        import ipaddress
        
        # 按优先级排序IP地址
        def ip_priority(ip: str) -> int:
            try:
                ip_obj = ipaddress.ip_address(ip)
                
                # 最高优先级：公网IP
                if ip_obj.is_global:
                    return 1
                
                # 高优先级：常见的家庭/办公网络
                common_networks = [
                    ipaddress.ip_network('192.168.0.0/16'),   # 家庭网络
                    ipaddress.ip_network('10.0.0.0/8'),      # 企业网络
                    ipaddress.ip_network('172.16.0.0/12'),   # 企业网络（但要避免虚拟网络段）
                ]
                
                for network in common_networks:
                    if ip_obj in network:
                        # 进一步细分优先级
                        if ip.startswith('192.168.1.') or ip.startswith('192.168.0.'):
                            return 2  # 最常见的家庭网络
                        elif ip.startswith('192.168.'):
                            return 3  # 其他家庭网络
                        elif ip.startswith('10.'):
                            return 4  # 企业网络
                        else:
                            return 5  # 其他私有网络
                
                # 较低优先级：其他私有IP
                if ip_obj.is_private:
                    return 6
                
                # 最低优先级：其他地址
                return 7
                
            except ValueError:
                return 99  # 无效IP地址
        
        # 按优先级排序并返回最佳IP
        candidate_ips.sort(key=ip_priority)
        return candidate_ips[0]
    
    def _is_valid_local_ip(self, ip: str) -> bool:
        """验证IP地址是否为有效的本地IP，排除虚拟网络接口"""
        import ipaddress

        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # 排除回环地址和链路本地地址
            if ip_obj.is_loopback or ip_obj.is_link_local:
                return False
            
            # 排除常见的虚拟网络IP段
            virtual_networks = [
                # Docker默认网段
                ipaddress.ip_network('172.17.0.0/16'),
                ipaddress.ip_network('172.18.0.0/16'),
                ipaddress.ip_network('172.19.0.0/16'),
                ipaddress.ip_network('172.20.0.0/16'),
                # VMware默认网段
                ipaddress.ip_network('192.168.56.0/24'),
                ipaddress.ip_network('192.168.57.0/24'),
                # VirtualBox默认网段
                ipaddress.ip_network('192.168.100.0/24'),
                # Hyper-V默认网段
                ipaddress.ip_network('172.16.0.0/12'),
                # 其他常见虚拟网段
                ipaddress.ip_network('10.0.75.0/24'),    # Parallels
                ipaddress.ip_network('169.254.0.0/16'),  # APIPA
            ]
            
            # 检查是否在虚拟网络范围内
            for network in virtual_networks:
                if ip_obj in network:
                    return False
            
            return True
        except ValueError:
            return False

    async def _convert_tex_to_format(self, tex_path: str, provider: str, original_name: Optional[str]) -> ConversionResult:
        """将TEX文件转换为指定格式（底层都调用TEX转PDF接口，通过provider控制输出格式）"""
        converter = Converter(self.logger, self.file_handler)
        is_ai_marker = "aw." in self.api_endpoint or "dev" in self.api_endpoint
        extra_params = {"provider": provider, "ai_mark": "123wx123" if is_ai_marker else ""}
        
        tex_filename = os.path.basename(tex_path)
        # 所有调用都使用TEX转PDF接口，通过provider参数控制最终输出格式
        return await converter.convert_file(
            tex_path, 
            "pdf",  # 底层接口始终是TEX转PDF
            extra_params=extra_params, 
            original_name=original_name or tex_filename
        )

    def _schedule_file_cleanup(self, file_path: str, delay: int = 300):
        """安排文件清理"""
        import threading
        
        def delayed_remove(path):
            try:
                os.remove(path)
            except Exception:
                pass
        
        timer = threading.Timer(delay, delayed_remove, args=(file_path,))
        timer.daemon = True
        timer.start()
