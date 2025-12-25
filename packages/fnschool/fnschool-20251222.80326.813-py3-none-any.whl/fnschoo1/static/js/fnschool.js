$(document).ready(function () {
  var messages = $('.messages')
  if (messages.length) {
    messages.css({
      position: 'absolute',
      top: $('.navbar').height() * 1.45,
      width: '100%',
    })
    setTimeout(function () {
      messages.hide()
    }, 25000)
  }
  var close_btn = $('.btn-close')
  if (close_btn.length) {
    close_btn.on('click', function () {
      close_btn.closest('.alert').hide()
    })
  }
})

function make_highlight(query, time_data) {
  var highlight_elements = $(query)
  var highlight_elements_toggled = []
  highlight_elements.each(function (index, element) {
    var element = $(element)
    var time_value = element.data(time_data)
    var seconds_diff = Math.floor((new Date() - new Date(time_value)) / 1000)
    if (seconds_diff < 46) {
      highlight_elements_toggled.push(element)
      element.toggleClass('fn-highlight')
      var table_container = $(element.closest('.table-container'))
      if (table_container.length) {
        var container = table_container
        var thead = $(element.closest('table').find('thead'))
        var pos =
          element.offset().top -
          container.offset().top +
          container.scrollTop() -
          thead.height()
        container.animate({ scrollTop: pos }, 1)
      }
    }
  })

  setTimeout(function () {
    $(highlight_elements_toggled).each(function (index, element) {
      element = $(element)
      element.toggleClass('fn-highlight')
    })
  }, 10 * 1000)
}

function get_cookie(name) {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=')
    if (cookieName === name) {
      return decodeURIComponent(cookieValue)
    }
  }
  return null
}
function delete_cookie(name) {
  document.cookie = name + `=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

function set_cookies(cookies) {
  cookies = new Map(Object.entries(cookies))
  for (var [key, value] of cookies) {
    set_simple_cookie(key, value)
  }
}

function set_simple_cookie(key, value) {
  cookie_enabled = get_cookie('cookie_enabled')
  if (cookie_enabled != '1') {
    return
  }
  const expiryDate = new Date()
  expiryDate.setFullYear(expiryDate.getFullYear() + 20)
  document.cookie = `${key}=${value}; expires=${expiryDate.toUTCString()}; path=/`
}
function update_href(query) {
  query = new Map(Object.entries(query))
  var url = new URL(window.location.href)
  var params = new URLSearchParams(url.search)
  for (var [key, value] of query) {
    params.set(key, value)
  }

  for (var [key, value] of params) {
    if (value === undefined || value === '' || value === null) {
      params.delete(key)
    }
  }

  url.search = params.toString()
  window.location.href = url.href
}
function open_small_window(url) {
  const size_times = 1 / 4
  const width = Math.round(screen.width * size_times)
  const height = Math.round(screen.height * size_times)
  const left = Math.round((screen.width - width) / 2)
  const _top = Math.round((screen.height - height) / 2)

  const left0 = Math.round((screen.width - height) / 2)
  const _top0 = Math.round((screen.height - width) / 2)

  var _width_ = width
  var _height_ = Math.round(height * 1.2)
  var _left_ = left
  var _top_ = _top

  const windowFeatures = `width=${_width_},height=${_height_},left=${_left_},top=${_top_},resizable=yes,scrollbars=yes`
  window.open(url, '_blank', windowFeatures)
}

document.addEventListener('DOMContentLoaded', function () {
  if (!document.cookie.includes('cookie_enabled=1')) {
    document.getElementById('cookieConsent').style.display = 'block'
  }

  var accept_cookies_element = document.getElementById('acceptCookies')
  if (accept_cookies_element != undefined) {
    accept_cookies_element.addEventListener('click', function () {
      const expiryDate = new Date()
      expiryDate.setFullYear(expiryDate.getFullYear() + 20)
      document.cookie = `cookie_enabled=1; expires=${expiryDate.toUTCString()}; path=/`
      document.getElementById('cookieConsent').style.display = 'none'
    })
  }
  var reject_cookies_element = document.getElementById('rejectCookies')
  if (reject_cookies_element != undefined) {
    reject_cookies_element.addEventListener('click', function () {
      document.getElementById('cookieConsent').style.display = 'none'
    })
  }
})

function set_page_size() {
  const page_size = document.querySelector('#page_size').value
  set_simple_cookie('page_size', page_size)
  update_href({ per_page: page_size })
}

$(document).ready(function () {
  page_size_forms = $('[name="page_size"]')
  if (page_size_forms.length > 0) {
    page_size_forms.on('submit', function (event) {
      event.preventDefault()
      set_page_size()
    })
  }
})

function set_page(num) {
  update_href({ page: num })
}

// The end.
