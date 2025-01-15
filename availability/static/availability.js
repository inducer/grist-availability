function styleEvent(ev) {
  if (ev.extendedProps.type === 'slot') {
    if (ev.extendedProps.available === true) {
      ev.setProp('color', 'limegreen');
      ev.setProp('title', 'Available');
    } else if (ev.extendedProps.available === false) {
      ev.setProp('color', 'red');
      ev.setProp('title', 'Unavailable');
    } else if (ev.extendedProps.available === null) {
      ev.setProp('color', null);
      ev.setProp('title', 'No Answer');
    }
  } else if (ev.extendedProps.type === 'span') {
    if (ev.extendedProps.maybe) {
      ev.setProp('color', 'orange');
      ev.setProp('title', 'If I must');
    } else {
      ev.setProp('color', 'green');
      ev.setProp('title', 'Available');
    }
  }
}

function eventClick(info) {
  const ev = info.event;
  if (ev.extendedProps.type === 'slot' && !info.jsEvent.shiftKey) {
    if (ev.extendedProps.available === null) {
      ev.setExtendedProp('available', true);
    } else if (ev.extendedProps.available) {
      ev.setExtendedProp('available', false);
    } else if (!ev.extendedProps.available) {
      ev.setExtendedProp('available', null);
    }
  }
  if (ev.extendedProps.type === 'span') {
    if (info.jsEvent.shiftKey) {
      ev.remove();
    // eslint-disable-next-line no-undef
    } else if (allowMaybe) {
      ev.setExtendedProp('maybe', !ev.extendedProps.maybe);
    }
  }
  styleEvent(ev);
}

function calSelect(info) {
  const ev = info.view.calendar.addEvent({
    start: info.start,
    end: info.end,
    editable: true,
    extendedProps: { type: 'span', maybe: false },
  });
  styleEvent(ev);
}

function fullcalDateToISO(date, calendar) {
  // eslint-disable-next-line no-undef
  return FullCalendar.Luxon3.toLuxonDateTime(date, calendar).toISO();
}

function onSubmit() {
  const slots = [];
  const spans = [];

  const cal = document.calendarInstance;

  cal.getEvents().forEach((ev) => {
    if (ev.extendedProps.type === 'slot') {
      slots.push({
        rspan_id: ev.extendedProps.rspan_id,
        start: fullcalDateToISO(ev.start, cal),
        end: fullcalDateToISO(ev.end, cal),
        available: ev.extendedProps.available,
      });
    } else if (ev.extendedProps.type === 'span') {
      spans.push({
        start: fullcalDateToISO(ev.start, cal),
        end: fullcalDateToISO(ev.end, cal),
        maybe: ev.extendedProps.maybe,
      });
    }
  });

  document.getElementById('calendarState').value = JSON.stringify({
    slots,
    spans,
  });

  document.getElementById('submitButton').classList.add('disabled');
  document.getElementById('calendarForm').submit();
}

// eslint-disable-next-line no-unused-vars
function initialize(initialDate, nDays, events, hasSpans, timezones) {
  document.addEventListener(
    'DOMContentLoaded',
    () => {
      const calendarEl = document.getElementById('calendar');
      // eslint-disable-next-line no-undef
      const calendar = new FullCalendar.Calendar(calendarEl, {
        // plugins: [timeGridPlugin],
        timeZone: timezones[0],
        initialView: 'timeGridNDay',
        headerToolbar: {
          start: false,
          center: false,
          end: false,
        },
        views: {
          timeGridNDay: {
            type: 'timeGrid',
            duration: { days: nDays },
          },
        },
        dayHeaderFormat: {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          omitCommas: true,
        },
        events,
        allDaySlot: false,
        initialDate,
        eventClick,
        selectable: hasSpans,
        select: calSelect,
      });
      calendar.getEvents().forEach(styleEvent);
      calendar.render();

      document.calendarInstance = calendar;
      document.getElementById('submitButton').addEventListener('click', onSubmit);
      document.getElementById('calPreviousButton').addEventListener('click', () => {
        calendar.prev();
      });
      document.getElementById('calNextButton').addEventListener('click', () => {
        calendar.next();
      });

      const tzSelect = document.getElementById('timezone');
      for (let i = 0; i < timezones.length; i += 1) {
        const opt = document.createElement('option');
        const tzName = timezones[i];
        opt.value = tzName;
        opt.innerHTML = tzName;
        tzSelect.appendChild(opt);
      }

      tzSelect.addEventListener('change', () => {
        calendar.setOption('timeZone', tzSelect.value);
      });
    },
  );
}

// vim: foldmethod=marker
