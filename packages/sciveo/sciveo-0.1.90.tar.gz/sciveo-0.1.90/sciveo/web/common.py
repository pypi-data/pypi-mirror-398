from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.db.models import Q, Case, Value, When, IntegerField
from sciveo.tools.logger import *


class SinglePage_:
  def __init__(self, object_list):
    self.object_list = object_list

class SinglePaginator_:
  def __init__(self, object_list):
    self.object_list = object_list
    self.count = -1
    self.num_pages = -1

  def page(self, page_num):
    return SinglePage_(self.object_list)

def filter_query(request, model_objects, list_query):
  filter_dict = {}
  for q in list_query:
    if q in request.GET:
      q_list = request.GET.getlist(q)
      filter_dict[f"{q}__in"] = q_list
  model_objects = model_objects.filter(**filter_dict)

  query_objects = []
  for q in list_query:
    negative_q = f"~{q}"
    if negative_q in request.GET:
      q_list = request.GET.getlist(negative_q)
      for q_value in q_list:
        query_objects.append(~Q(**{q: q_value}))
  if len(query_objects) > 0:
    query = query_objects.pop()
    for q_obj in query_objects:
      query &= q_obj
    model_objects = model_objects.filter(query)

  return model_objects

def admin_required(view_func):
  def wrapper_func(request, *args, **kwargs):
    if request.user.is_authenticated and request.user.is_superuser:
      return view_func(request, *args, **kwargs)
    else:
      return HttpResponseForbidden()
  return wrapper_func

def data_model_to_dict(object, fields=None, recursive=True):
  data = model_to_dict(object, fields=fields)

  for k in ["created_at", "updated_at"]:
    if hasattr(object, k):
      data[k] = getattr(object, k)

  for k, v in data.items():
    if isinstance(v, list):
      if recursive:
        data[k] = [data_model_to_dict(obj, fields, recursive) for obj in v]
      else:
        data[k] = [str(obj) for obj in v]
  return data

def paginated(request, model_objects, order_default="'id'", already_paginated=False):
  page_current = int(request.GET.get('page', 1))
  page_limit = int(request.GET.get('limit', 10))
  order = request.GET.get('order', order_default)[1:-1]
  fields = request.GET.get('fields', None)
  recursive = "recursive" in request.GET

  try:
    if already_paginated:
      paginator = SinglePaginator_(model_objects)
    else:
      paginator = Paginator(model_objects.order_by(order), page_limit)

    page = paginator.page(page_current)

    data = [data_model_to_dict(obj, fields, recursive) for obj in page.object_list]

    result = {
      "pagination": {
        'page': page_current,
        'limit': page_limit,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
      },
      "data": data
    }
  except Exception as e:
    error("paginated", e)
    result = {"error": str(e)}

  return JsonResponse(result)


def filter_on_list(queryset, column_name, filter_list):
  """
  Filters the given queryset based on the values of the specified column
  according to the filter_list.

  Args:
    queryset (QuerySet): The queryset to be sorted.
    column_name (str): The name of the column to sort on.
    filter_list (list): The list defining the desired order.

  Returns:
    QuerySet: The filtered queryset.
  """
  return queryset.filter(Q(**{column_name + '__in': filter_list}))

def sort_on_list(queryset, column_name, sort_list):
  """
  Sorts the given queryset based on the values of the specified column
  according to the order defined in the sort_list.

  Args:
    queryset (QuerySet): The queryset to be sorted.
    column_name (str): The name of the column to sort on.
    sort_list (list): The list defining the desired order.

  Returns:
    QuerySet: The sorted queryset.
  """
  # Create a Case/When expression for each value in the desired order
  # Assign a numerical value to each item in the list
  # Use the Case/When expression to annotate each object with its numerical value
  # Use the annotated value to order the queryset
  return queryset.annotate(
    custom_order=Case(
      *[When(**{column_name: value}, then=Value(index)) for index, value in enumerate(sort_list)],
      default=Value(len(sort_list)),
      output_field=IntegerField()
    )
  ).order_by('custom_order')
