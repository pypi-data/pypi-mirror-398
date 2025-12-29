import requests
from typing import Optional, Dict
import names


class NameGenerator:
    """姓名生成器，支持英文和中文姓名生成，支持多种生成方式"""

    def __init__(self, use_api: bool = False, language: str = "en"):
        """
        description:
            初始化姓名生成器，设置生成方式（API或本地库）和语言
        parameters:
            use_api(bool): 是否使用API方式，True表示使用randomuser.me API，False表示使用本地库
            language(str): 语言设置，"en"表示英文，"zh"表示中文，默认为"en"
        return:
            无
        """
        self.use_api = use_api
        self.api_url = "https://randomuser.me/api/"
        self.language = language
        self._faker_zh = None

    def _generate_random_name_api(self) -> Optional[Dict[str, str]]:
        """
        description:
            使用 randomuser.me API 获取随机姓名（支持英文和中文）
            注意：API不支持中文名，当language="zh"时，如果API返回非中文名则返回None，由调用方降级到本地生成
        parameters:
            无
        return:
            name(Optional[Dict[str, str]]): 包含first_name、last_name、full_name的字典，如果API调用失败或返回非中文名则返回None
        """
        try:
            # randomuser.me API 不支持中文名生成，当需要中文名时直接返回None，降级到本地生成
            if self.language == "zh":
                return None
            
            params = {
                "nat": "us,gb,au,ca",  # 限制为英语国家
                "inc": "name",  # 只获取姓名信息
            }
            response = requests.get(self.api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                user = data["results"][0]
                first_name = user["name"]["first"]
                last_name = user["name"]["last"]

                # 英文名格式：名字 姓氏（有空格）
                full_name = f"{first_name} {last_name}"

                return {
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name,
                }
            return None
        except requests.exceptions.RequestException:
            return None
        except (KeyError, IndexError):
            return None

    def _get_faker_zh(self):
        """
        description:
            获取或创建中文 Faker 实例（延迟导入）
        return:
            Faker: 中文 Faker 实例
        """
        if self._faker_zh is None:
            from faker import Faker
            self._faker_zh = Faker("zh_CN")
        return self._faker_zh

    def _generate_random_name_local_chinese(self) -> Dict[str, str]:
        """
        description:
            使用本地方式生成随机中文姓名（使用 Faker 库）
        parameters:
            无
        return:
            name(Dict[str, str]): 包含first_name、last_name、full_name的字典
        """
        # 使用 Faker 库生成中文名
        # Faker 的 last_name() 返回姓氏，first_name() 返回名字
        faker = self._get_faker_zh()
        last_name = faker.last_name()
        first_name = faker.first_name()
        
        # 中文名格式：姓氏+名字（无空格）
        full_name = f"{last_name}{first_name}"
        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
        }

    def _generate_random_name_local_english(self) -> Dict[str, str]:
        """
        description:
            使用本地方式生成随机英文姓名
        parameters:
            无
        return:
            name(Dict[str, str]): 包含first_name、last_name、full_name的字典
        """
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        # 英文名格式：名字 姓氏（有空格）
        full_name = f"{first_name} {last_name}"
        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
        }

    def _generate_random_name_local(self) -> Dict[str, str]:
        """
        description:
            使用本地方式生成随机姓名（根据语言设置选择生成方式）
        parameters:
            无
        return:
            name(Dict[str, str]): 包含first_name、last_name、full_name的字典
        """
        if self.language == "zh":
            return self._generate_random_name_local_chinese()
        else:
            return self._generate_random_name_local_english()

    def generate_random_name(self) -> Dict[str, str]:
        """
        description:
            生成随机姓名（支持英文和中文），根据初始化时的设置选择API方式或本地方式，API失败时自动降级到本地方式
        parameters:
            无
        return:
            name(Dict[str, str]): 包含first_name、last_name、full_name的字典
        """
        name = self._generate_random_name_api() if self.use_api else None
        return name or self._generate_random_name_local()
