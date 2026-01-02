from finter.data import ModelData, Symbol
from finter.framework_model.submission.config import ModelUniverseConfig


class PositionData:
    def __init__(self, model_id):
        self.model_id = model_id
        self.universe = ModelUniverseConfig.find_universe_by_model_id(model_id)

        self.origin_position = ModelData.load(self.model_id)
        self.symbol = Symbol(self.universe.name.lower())

        if self.universe.name.lower() == "kr_stock":
            self.id_ticker_map = lambda: self.symbol._id_table["STK_CD"].to_dict()
            self.id_name_map = lambda: self.symbol._id_table["STK_NM_KOR"].to_dict()
            self.ticker_id_map = (
                lambda: self.symbol._id_table.reset_index()
                .set_index("STK_CD")["ccid"]
                .to_dict()
            )
        elif self.universe.name.lower() == "us_stock":
            self.id_ticker_map = lambda: self.symbol._id_table["tic"].to_dict()
            self.id_name_map = lambda: self.symbol._id_table["conml"].to_dict()
            self.ticker_id_map = (
                lambda: self.symbol._id_table.reset_index()
                .set_index("tic")["gvkeyiid"]
                .to_dict()
            )
        else:
            raise ValueError(f"Invalid universe: {self.universe.name.lower()}")

    def load(self, column_type: str = "original"):
        if column_type == "original":
            return self.origin_position

        if column_type == "ticker":
            id_ticker_map = self.id_ticker_map()
            return self.origin_position.rename(columns=id_ticker_map)

        if column_type == "name":
            id_name_map = self.id_name_map()
            return self.origin_position.rename(columns=id_name_map)


if __name__ == "__main__":
    model_id = "alpha.krx.krx.stock.ldh0127.bb_ls_1"
    self = PositionData(model_id)
    print(self.origin_position)

    model_id = "alpha.us.compustat.stock.ldh0127.tt_1"
    self = PositionData(model_id)
    print(self.load(column_type="ticker"))
