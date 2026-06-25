from datetime import datetime
from decimal import Decimal

import pytest

from bibip_car_service import CarService
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


@pytest.fixture
def car_data():
    return [
        Car(
            vin="KNAGM4A77D5316538",
            model=1,
            price=Decimal("2000"),
            date_start=datetime(2024, 2, 8),
            status=CarStatus.available,
        ),
        Car(
            vin="5XYPH4A10GG021831",
            model=2,
            price=Decimal("2300"),
            date_start=datetime(2024, 2, 20),
            status=CarStatus.reserve,
        ),
        Car(
            vin="KNAGH4A48A5414970",
            model=1,
            price=Decimal("2100"),
            date_start=datetime(2024, 4, 4),
            status=CarStatus.available,
        ),
        Car(
            vin="JM1BL1TFXD1734246",
            model=3,
            price=Decimal("2276.65"),
            date_start=datetime(2024, 5, 17),
            status=CarStatus.available,
        ),
        Car(
            vin="JM1BL1M58C1614725",
            model=3,
            price=Decimal("2549.10"),
            date_start=datetime(2024, 5, 17),
            status=CarStatus.reserve,
        ),
        Car(
            vin="KNAGR4A63D5359556",
            model=1,
            price=Decimal("2376"),
            date_start=datetime(2024, 5, 17),
            status=CarStatus.available,
        ),
        Car(
            vin="5N1CR2MN9EC641864",
            model=4,
            price=Decimal("3100"),
            date_start=datetime(2024, 6, 1),
            status=CarStatus.available,
        ),
        Car(
            vin="JM1BL1L83C1660152",
            model=3,
            price=Decimal("2635.17"),
            date_start=datetime(2024, 6, 1),
            status=CarStatus.available,
        ),
        Car(
            vin="5N1CR2TS0HW037674",
            model=4,
            price=Decimal("3100"),
            date_start=datetime(2024, 6, 1),
            status=CarStatus.available,
        ),
        Car(
            vin="5N1AR2MM4DC605884",
            model=4,
            price=Decimal("3200"),
            date_start=datetime(2024, 7, 15),
            status=CarStatus.available,
        ),
        Car(
            vin="VF1LZL2T4BC242298",
            model=5,
            price=Decimal("2280.76"),
            date_start=datetime(2024, 8, 31),
            status=CarStatus.delivery,
        ),
    ]


@pytest.fixture
def model_data():
    return [
        Model(id=1, name="Optima", brand="Kia"),
        Model(id=2, name="Sorento", brand="Kia"),
        Model(id=3, name="3", brand="Mazda"),
        Model(id=4, name="Pathfinder", brand="Nissan"),
        Model(id=5, name="Logan", brand="Renault"),
    ]


class TestCarServiceScenarios:
    def _fill_initial_data(self, service: CarService, car_data: list[Car], model_data: list[Model]) -> None:
        for model in model_data:
            service.add_model(model)

        for car in car_data:
            service.add_car(car)

    def test_add_new_car(self, tmpdir: str, car_data: list[Car], model_data: list[Model]) -> None:
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        assert True

    def test_sell_car(self, tmpdir: str, car_data: list[Car], model_data: list[Model]) -> None:
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        sale = Sale(
            sales_number="20240903#JM1BL1M58C1614725",
            car_vin="JM1BL1M58C1614725",
            sales_date=datetime(2024, 9, 3),
            cost=Decimal("2399.99"),
        )
        service.sell_car(sale)

        res = service.get_car_info("JM1BL1M58C1614725")
        assert res is not None
        assert res.status == CarStatus.sold

    def test_list_cars_by_available_status(self, tmpdir: str, car_data: list[Car], model_data: list[Model]):
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        available_cars = [car for car in car_data if car.status == CarStatus.available]

        assert service.get_cars(CarStatus.available) == available_cars

    def test_list_full_info_by_vin(self, tmpdir: str, car_data: list[Car], model_data: list[Model]):
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        full_info_no_sale = CarFullInfo(
            vin="KNAGM4A77D5316538",
            car_model_name="Optima",
            car_model_brand="Kia",
            price=Decimal("2000"),
            date_start=datetime(2024, 2, 8),
            status=CarStatus.available,
            sales_date=None,
            sales_cost=None,
        )

        assert service.get_car_info("KNAGM4A77D5316538") == full_info_no_sale

        sale = Sale(
            sales_number="20240903#KNAGM4A77D5316538",
            car_vin="KNAGM4A77D5316538",
            sales_date=datetime(2024, 9, 3),
            cost=Decimal("2999.99"),
        )

        service.sell_car(sale)

        full_info_with_sale = CarFullInfo(
            vin="KNAGM4A77D5316538",
            car_model_name="Optima",
            car_model_brand="Kia",
            price=Decimal("2000"),
            date_start=datetime(2024, 2, 8),
            status=CarStatus.sold,
            sales_date=sale.sales_date,
            sales_cost=sale.cost,
        )

        assert service.get_car_info("KNAGM4A77D5316538") == full_info_with_sale

    def test_update_vin(self, tmpdir: str, car_data: list[Car], model_data: list[Model]):
        service = CarService(tmpdir)

        full_info_no_sale = CarFullInfo(
            vin="KNAGM4A77D5316538",
            car_model_name="Optima",
            car_model_brand="Kia",
            price=Decimal("2000"),
            date_start=datetime(2024, 2, 8),
            status=CarStatus.available,
            sales_date=None,
            sales_cost=None,
        )

        self._fill_initial_data(service, car_data, model_data)

        assert service.get_car_info("KNAGM4A77D5316538") == full_info_no_sale
        assert service.get_car_info("UPDGM4A77D5316538") is None

        service.update_vin("KNAGM4A77D5316538", "UPDGM4A77D5316538")

        full_info_no_sale.vin = "UPDGM4A77D5316538"
        assert service.get_car_info("UPDGM4A77D5316538") == full_info_no_sale
        assert service.get_car_info("KNAGM4A77D5316538") is None

    def test_delete_sale(self, tmpdir: str, car_data: list[Car], model_data: list[Model]):
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        sale = Sale(
            sales_number="20240903#KNAGM4A77D5316538",
            car_vin="KNAGM4A77D5316538",
            sales_date=datetime(2024, 9, 3),
            cost=Decimal("2999.99"),
        )

        service.sell_car(sale)

        car = service.get_car_info("KNAGM4A77D5316538")
        assert car is not None
        assert car.status == CarStatus.sold

        service.revert_sale("20240903#KNAGM4A77D5316538")

        car = service.get_car_info("KNAGM4A77D5316538")
        assert car is not None
        assert car.status == CarStatus.available

    def test_top_3_models_by_sales(self, tmpdir: str, car_data: list[Car], model_data: list[Model]):
        service = CarService(tmpdir)

        self._fill_initial_data(service, car_data, model_data)

        sales = [
            Sale(
                sales_number="20240903#KNAGM4A77D5316538",
                car_vin="KNAGM4A77D5316538",
                sales_date=datetime(2024, 9, 3),
                cost=Decimal("1999.09"),
            ),
            Sale(
                sales_number="20240903#KNAGH4A48A5414970",
                car_vin="KNAGH4A48A5414970",
                sales_date=datetime(2024, 9, 4),
                cost=Decimal("2100"),
            ),
            Sale(
                sales_number="20240903#KNAGR4A63D5359556",
                car_vin="KNAGR4A63D5359556",
                sales_date=datetime(2024, 9, 5),
                cost=Decimal("7623"),
            ),
            Sale(
                sales_number="20240903#JM1BL1M58C1614725",
                car_vin="JM1BL1M58C1614725",
                sales_date=datetime(2024, 9, 6),
                cost=Decimal("2334"),
            ),
            Sale(
                sales_number="20240903#JM1BL1L83C1660152",
                car_vin="JM1BL1L83C1660152",
                sales_date=datetime(2024, 9, 7),
                cost=Decimal("451"),
            ),
            Sale(
                sales_number="20240903#5N1CR2TS0HW037674",
                car_vin="5N1CR2TS0HW037674",
                sales_date=datetime(2024, 9, 8),
                cost=Decimal("9876"),
            ),
            Sale(
                sales_number="20240903#5XYPH4A10GG021831",
                car_vin="5XYPH4A10GG021831",
                sales_date=datetime(2024, 9, 9),
                cost=Decimal("1234"),
            ),
        ]

        for sale in sales:
            service.sell_car(sale)

        top_3_models = [
            ModelSaleStats(car_model_name="Optima", brand="Kia", sales_number=3),
            ModelSaleStats(car_model_name="3", brand="Mazda", sales_number=2),
            ModelSaleStats(car_model_name="Pathfinder", brand="Nissan", sales_number=1),
        ]
        assert service.top_models_by_sales() == top_3_models
