# Impelement of quick sort algorithm refers to https://www.cnblogs.com/kevinbee/p/18678275 .


def _swap(a, b):
	return b, a


def _qsort_partition(arr, low, high):
	pivot = arr[high]
	
	i = low - 1
	for j in range(low, high):
		if arr[j] < pivot:
			i += 1
			arr[i], arr[j] = _swap(arr[i], arr[j])

	arr[i + 1], arr[high] = _swap(arr[i + 1], arr[high])
	return i + 1


def _qsort(arr, low, high):
	if low < high:
		pi = _qsort_partition(arr, low, high)

		_qsort(arr, low, pi - 1)
		_qsort(arr, pi + 1, high)


def qsort(arr):
	qsort(arr, 0, len(arr) - 1)
