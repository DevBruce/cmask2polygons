import cv2
import numpy as np


__all__ = ['get_polygons_per_class']


def _get_unique_colors(img_arr):
    return np.unique(img_arr.reshape(-1, img_arr.shape[2]), axis=0)


def _get_cls_from_color_mask(color_mask, cls_color_map):
    cls_color_map_rev = {str(color): cls_name for cls_name, color in cls_color_map.items()}
    colors = _get_unique_colors(img_arr=color_mask)
    classes = list()
    for color in colors:
        color = str(tuple(color))  # Convert color type to str for hashing
        cls = cls_color_map_rev[color]
        classes.append(cls)
    return classes


def _get_bin_mask(color_mask, cls_name, cls_color_map):
    mask = color_mask.copy()
    color = cls_color_map[cls_name]
    cls_pixels = np.all(mask==color, axis=-1)

    mask[cls_pixels] = [255, 255, 255]
    mask[~cls_pixels] = [0, 0, 0]
    return mask


def _get_polygons_from_bin_mask(bin_mask, min_area, epsilon_param):
    contours, _ = cv2.findContours(bin_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)  # contours, hierarchy

    contour_approxed_list = list()
    for contour in contours:
        if cv2.contourArea(contour) < min_area: continue
        epsilon = epsilon_param * cv2.arcLength(curve=contour, closed=True)
        contour_approxed = cv2.approxPolyDP(curve=contour, epsilon=epsilon, closed=True)

        # Convert data type of contours for serializing (np.ndarray --> list, np.int64 --> int)
        contour_approxed_converted = list()
        for xy in contour_approxed:
            xy = list(map(int, xy[0]))
            contour_approxed_converted.append(xy)

        # Append end point for representing closed
        contour_approxed_converted.append(contour_approxed_converted[0])
        
        contour_approxed_list.append(contour_approxed_converted)
    return contour_approxed_list


def get_polygons_per_class(color_mask, cls_color_map, min_area=100.0, epsilon_param=8e-4):
    classes = _get_cls_from_color_mask(color_mask=color_mask, cls_color_map=cls_color_map)

    polygons_per_class = dict()
    for cls in classes:
        bin_mask = _get_bin_mask(color_mask=color_mask, cls_name=cls, cls_color_map=cls_color_map)
        bin_mask = cv2.cvtColor(bin_mask, cv2.COLOR_RGB2GRAY)
        polygons = _get_polygons_from_bin_mask(bin_mask=bin_mask, min_area=min_area, epsilon_param=epsilon_param)
        polygons_per_class[cls] = polygons
    return polygons_per_class