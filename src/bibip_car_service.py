from __future__ import annotations

import os
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale

T = TypeVar("T", bound=BaseModel)


class CarService:
    RECORD_SIZE = 500
    RECORD_SEPARATOR = b"\n"

    CARS_FILE = "cars.txt"
    CARS_INDEX_FILE = "cars_index.txt"
    MODELS_FILE = "models.txt"
    MODELS_INDEX_FILE = "models_index.txt"
    SALES_FILE = "sales.txt"
    SALES_INDEX_FILE = "sales_index.txt"

    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        Path(self.root_directory_path).mkdir(parents=True, exist_ok=True)

    # Низкоуровневая работа с файлами
    def _path(self, file_name: str) -> str:
        return os.path.join(self.root_directory_path, file_name)

    def _record_length(self) -> int:
        return self.RECORD_SIZE + len(self.RECORD_SEPARATOR)

    def _serialize(self, obj: BaseModel) -> bytes:
        raw = obj.model_dump_json().encode("utf-8")
        if len(raw) > self.RECORD_SIZE:
            raise ValueError("Record is longer than fixed record size")
        return raw.ljust(self.RECORD_SIZE, b" ") + self.RECORD_SEPARATOR

    def _append_record(self, file_name: str, obj: BaseModel) -> int:
        path = self._path(file_name)
        if os.path.exists(path):
            line_number = os.path.getsize(path) // self._record_length()
        else:
            line_number = 0

        with open(path, "ab") as file:
            file.write(self._serialize(obj))

        return line_number

    def _read_record(
        self, file_name: str, line_number: int, model_cls: type[T]
    ) -> T | None:
        path = self._path(file_name)
        if not os.path.exists(path):
            return None

        with open(path, "rb") as file:
            file.seek(line_number * self._record_length())
            raw = file.read(self.RECORD_SIZE)

        raw = raw.rstrip(b" ")
        if not raw:
            return None
        return model_cls.model_validate_json(raw.decode("utf-8"))

    def _write_record(self, file_name: str, line_number: int, obj: BaseModel) -> None:
        path = self._path(file_name)
        with open(path, "r+b") as file:
            file.seek(line_number * self._record_length())
            file.write(self._serialize(obj))

    def _read_all_records(self, file_name: str, model_cls: type[T]) -> list[T]:
        path = self._path(file_name)
        if not os.path.exists(path):
            return []

        result: list[T] = []
        with open(path, "rb") as file:
            while True:
                raw = file.read(self.RECORD_SIZE)
                if not raw:
                    break
                file.read(len(self.RECORD_SEPARATOR))
                raw = raw.rstrip(b" ")
                if raw:
                    result.append(model_cls.model_validate_json(raw.decode("utf-8")))
        return result

    def _read_index(self, index_file_name: str) -> dict[str, int]:
        path = self._path(index_file_name)
        if not os.path.exists(path):
            return {}

        index: dict[str, int] = {}
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                key, line_number = line.split(";")
                index[key] = int(line_number)
        return index

    def _write_index(self, index_file_name: str, index: dict[str, int]) -> None:
        path = self._path(index_file_name)
        with open(path, "w", encoding="utf-8") as file:
            for key in sorted(index):
                file.write(f"{key};{index[key]}\n")

    def _add_to_index(self, index_file_name: str, key: str, line_number: int) -> None:
        index = self._read_index(index_file_name)
        index[key] = line_number
        self._write_index(index_file_name, index)

    def _find_by_index(
        self, file_name: str, index_file_name: str, key: str, model_cls: type[T]
    ) -> T | None:
        index = self._read_index(index_file_name)
        line_number = index.get(key)
        if line_number is None:
            return None
        return self._read_record(file_name, line_number, model_cls)

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        line_number = self._append_record(self.MODELS_FILE, model)
        self._add_to_index(self.MODELS_INDEX_FILE, str(model.id), line_number)
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        line_number = self._append_record(self.CARS_FILE, car)
        self._add_to_index(self.CARS_INDEX_FILE, car.vin, line_number)
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        car_index = self._read_index(self.CARS_INDEX_FILE)
        car_line_number = car_index.get(sale.car_vin)
        if car_line_number is None:
            raise ValueError(f"Car with VIN {sale.car_vin} was not found")

        car = self._read_record(self.CARS_FILE, car_line_number, Car)
        if car is None:
            raise ValueError(f"Car with VIN {sale.car_vin} was not found")

        sold_car = car.model_copy(update={"status": CarStatus.sold})
        self._write_record(self.CARS_FILE, car_line_number, sold_car)

        sale_line_number = self._append_record(self.SALES_FILE, sale)
        # В задании удаление продажи происходит по sales_number, поэтому индексируем продажи по sales_number.
        self._add_to_index(self.SALES_INDEX_FILE, sale.sales_number, sale_line_number)

        return sold_car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars = self._read_all_records(self.CARS_FILE, Car)
        return [car for car in cars if car.status == status]

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car = self._find_by_index(self.CARS_FILE, self.CARS_INDEX_FILE, vin, Car)
        if car is None:
            return None

        model = self._find_by_index(
            self.MODELS_FILE, self.MODELS_INDEX_FILE, str(car.model), Model
        )
        if model is None:
            raise ValueError(f"Model with id {car.model} was not found")

        sale_for_car = None
        for sale in self._read_all_records(self.SALES_FILE, Sale):
            if sale.car_vin == vin:
                sale_for_car = sale
                break

        return CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sale_for_car.sales_date if sale_for_car else None,
            sales_cost=sale_for_car.cost if sale_for_car else None,
        )

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        car_index = self._read_index(self.CARS_INDEX_FILE)
        line_number = car_index.get(vin)
        if line_number is None:
            raise ValueError(f"Car with VIN {vin} was not found")
        if new_vin in car_index:
            raise ValueError(f"Car with VIN {new_vin} already exists")

        car = self._read_record(self.CARS_FILE, line_number, Car)
        if car is None:
            raise ValueError(f"Car with VIN {vin} was not found")

        updated_car = car.model_copy(update={"vin": new_vin})
        self._write_record(self.CARS_FILE, line_number, updated_car)

        del car_index[vin]
        car_index[new_vin] = line_number
        self._write_index(self.CARS_INDEX_FILE, car_index)

        # На случай если VIN меняют уже после продажи: обновим связанные продажи и их файл.
        sales = self._read_all_records(self.SALES_FILE, Sale)
        for sale_line_number, sale in enumerate(sales):
            if sale.car_vin == vin:
                updated_sale = sale.model_copy(update={"car_vin": new_vin})
                self._write_record(self.SALES_FILE, sale_line_number, updated_sale)

        return updated_car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_index = self._read_index(self.SALES_INDEX_FILE)
        sale_line_number = sales_index.get(sales_number)
        if sale_line_number is None:
            raise ValueError(f"Sale {sales_number} was not found")

        sale = self._read_record(self.SALES_FILE, sale_line_number, Sale)
        if sale is None:
            raise ValueError(f"Sale {sales_number} was not found")

        # Физически удаляем продажу: переписываем файл sales.txt без этой строки
        sales = self._read_all_records(self.SALES_FILE, Sale)
        remaining_sales = [item for item in sales if item.sales_number != sales_number]
        with open(self._path(self.SALES_FILE), "wb") as file:
            for item in remaining_sales:
                file.write(self._serialize(item))

        new_sales_index = {
            item.sales_number: line_number
            for line_number, item in enumerate(remaining_sales)
        }
        self._write_index(self.SALES_INDEX_FILE, new_sales_index)

        car_index = self._read_index(self.CARS_INDEX_FILE)
        car_line_number = car_index.get(sale.car_vin)
        if car_line_number is None:
            raise ValueError(f"Car with VIN {sale.car_vin} was not found")

        car = self._read_record(self.CARS_FILE, car_line_number, Car)
        if car is None:
            raise ValueError(f"Car with VIN {sale.car_vin} was not found")

        available_car = car.model_copy(update={"status": CarStatus.available})
        self._write_record(self.CARS_FILE, car_line_number, available_car)
        return available_car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        cars_by_vin = {
            car.vin: car for car in self._read_all_records(self.CARS_FILE, Car)
        }
        models_by_id = {
            model.id: model for model in self._read_all_records(self.MODELS_FILE, Model)
        }

        sales_count_by_model_id: dict[int, int] = defaultdict(int)
        max_sale_cost_by_model_id: dict[int, Decimal] = defaultdict(
            lambda: Decimal("0")
        )

        for sale in self._read_all_records(self.SALES_FILE, Sale):
            car = cars_by_vin.get(sale.car_vin)
            if car is None:
                continue
            sales_count_by_model_id[car.model] += 1
            if sale.cost > max_sale_cost_by_model_id[car.model]:
                max_sale_cost_by_model_id[car.model] = sale.cost

        sorted_model_ids = sorted(
            sales_count_by_model_id,
            key=lambda model_id: (
                -sales_count_by_model_id[model_id],
                -max_sale_cost_by_model_id[model_id],
            ),
        )

        result: list[ModelSaleStats] = []
        for model_id in sorted_model_ids[:3]:
            model = models_by_id.get(model_id)
            if model is None:
                continue
            result.append(
                ModelSaleStats(
                    car_model_name=model.name,
                    brand=model.brand,
                    sales_number=sales_count_by_model_id[model_id],
                )
            )
        return result
