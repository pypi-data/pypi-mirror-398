import os
from typing import List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class ModelInfo:
    def __init__(self):
        self.base_url = "https://api.finter.quantit.io"
        self.headers = {
            "accept": "application/json",
            "Authorization": f'Token {os.environ.get("FINTER_API_KEY")}',
        }

    def get_model_info(self, model_name: str) -> dict:
        """특정 모델의 상세 정보를 조회합니다."""
        url = f"{self.base_url}/model/model_info"
        response = requests.get(
            url, params={"identity_name": model_name}, headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get model info: {response.text}")

    def get_alpha_models(self) -> List[str]:
        """내가 가진 Alpha 모델 목록을 조회합니다."""
        url = f"{self.base_url}/alpha/identities"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("am_identity_name_list", [])
        else:
            raise Exception(f"Failed to get alpha models: {response.text}")

    def get_portfolio_models(self) -> List[str]:
        """내가 가진 Portfolio 모델 목록을 조회합니다."""
        url = f"{self.base_url}/portfolio/identities"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("pm_identity_name_list", [])
        else:
            raise Exception(f"Failed to get portfolio models: {response.text}")

    def get_fund_models(self) -> List[str]:
        """내가 가진 Fund 모델 목록을 조회합니다."""
        url = f"{self.base_url}/fund/identities"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("fund_identity_name_list", [])
        else:
            raise Exception(f"Failed to get fund models: {response.text}")

    def get_flexible_fund_models(self) -> List[str]:
        """내가 가진 Flexible Fund 모델 목록을 조회합니다."""
        url = f"{self.base_url}/flexiblefund/identities"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("fm_identity_name_list", [])
        else:
            raise Exception(f"Failed to get flexible fund models: {response.text}")

    def get_all_models(self) -> dict:
        """모든 종류의 모델 목록을 조회합니다."""
        return {
            "alpha": self.get_alpha_models(),
            "portfolio": self.get_portfolio_models(),
            "fund": self.get_fund_models(),
            "flexible_fund": self.get_flexible_fund_models(),
        }


if __name__ == "__main__":
    model_info = ModelInfo()
    print(model_info.get_model_info("portfolio.us.us.stock.shum.aristo1"))
