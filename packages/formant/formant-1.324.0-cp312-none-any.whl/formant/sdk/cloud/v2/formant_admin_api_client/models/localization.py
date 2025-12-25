from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.goal import Goal
  from ..models.map_ import Map
  from ..models.odometry import Odometry
  from ..models.path import Path
  from ..models.point_cloud import PointCloud




T = TypeVar("T", bound="Localization")

@attr.s(auto_attribs=True)
class Localization:
    """
    Attributes:
        odometry (Union[Unset, Odometry]):
        map_ (Union[Unset, Map]):
        point_clouds (Union[Unset, List['PointCloud']]):
        path (Union[Unset, Path]):
        goal (Union[Unset, Goal]):
        url (Union[Unset, str]):
        size (Union[Unset, int]):
    """

    odometry: Union[Unset, 'Odometry'] = UNSET
    map_: Union[Unset, 'Map'] = UNSET
    point_clouds: Union[Unset, List['PointCloud']] = UNSET
    path: Union[Unset, 'Path'] = UNSET
    goal: Union[Unset, 'Goal'] = UNSET
    url: Union[Unset, str] = UNSET
    size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        odometry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.odometry, Unset):
            odometry = self.odometry.to_dict()

        map_: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.map_, Unset):
            map_ = self.map_.to_dict()

        point_clouds: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.point_clouds, Unset):
            point_clouds = []
            for point_clouds_item_data in self.point_clouds:
                point_clouds_item = point_clouds_item_data.to_dict()

                point_clouds.append(point_clouds_item)




        path: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.path, Unset):
            path = self.path.to_dict()

        goal: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.goal, Unset):
            goal = self.goal.to_dict()

        url = self.url
        size = self.size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if odometry is not UNSET:
            field_dict["odometry"] = odometry
        if map_ is not UNSET:
            field_dict["map"] = map_
        if point_clouds is not UNSET:
            field_dict["pointClouds"] = point_clouds
        if path is not UNSET:
            field_dict["path"] = path
        if goal is not UNSET:
            field_dict["goal"] = goal
        if url is not UNSET:
            field_dict["url"] = url
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.goal import Goal
        from ..models.map_ import Map
        from ..models.odometry import Odometry
        from ..models.path import Path
        from ..models.point_cloud import PointCloud
        d = src_dict.copy()
        _odometry = d.pop("odometry", UNSET)
        odometry: Union[Unset, Odometry]
        if isinstance(_odometry,  Unset):
            odometry = UNSET
        else:
            odometry = Odometry.from_dict(_odometry)




        _map_ = d.pop("map", UNSET)
        map_: Union[Unset, Map]
        if isinstance(_map_,  Unset):
            map_ = UNSET
        else:
            map_ = Map.from_dict(_map_)




        point_clouds = []
        _point_clouds = d.pop("pointClouds", UNSET)
        for point_clouds_item_data in (_point_clouds or []):
            point_clouds_item = PointCloud.from_dict(point_clouds_item_data)



            point_clouds.append(point_clouds_item)


        _path = d.pop("path", UNSET)
        path: Union[Unset, Path]
        if isinstance(_path,  Unset):
            path = UNSET
        else:
            path = Path.from_dict(_path)




        _goal = d.pop("goal", UNSET)
        goal: Union[Unset, Goal]
        if isinstance(_goal,  Unset):
            goal = UNSET
        else:
            goal = Goal.from_dict(_goal)




        url = d.pop("url", UNSET)

        size = d.pop("size", UNSET)

        localization = cls(
            odometry=odometry,
            map_=map_,
            point_clouds=point_clouds,
            path=path,
            goal=goal,
            url=url,
            size=size,
        )

        localization.additional_properties = d
        return localization

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
