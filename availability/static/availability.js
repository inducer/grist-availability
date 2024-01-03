function eventClick(info) {
  const ev = info.event;
  if (!info.jsEvent.shiftKey) {
    if (ev.extendedProps.type === 'slot') {
      if (ev.extendedProps.available === null) {
        ev.setExtendedProp('available', true);
        ev.setProp('color', 'green');
        ev.setProp('title', 'Available');
      } else if (ev.extendedProps.available) {
        ev.setExtendedProp('available', false);
        ev.setProp('color', 'red');
        ev.setProp('title', 'Unavailable');
      } else if (!ev.extendedProps.available) {
        ev.setExtendedProp('available', null);
        ev.setProp('color', null);
        ev.setProp('title', 'No Answer');
      }
    }
  } else if (ev.extendedProps.type === 'span') {
    ev.remove();
  }
}

function calSelect(info) {
  info.view.calendar.addEvent({
    start: info.start,
    end: info.end,
    editable: true,
    color: 'orange',
    extendedProps: { type: 'span' },
  });
}

function onSubmit() {
  const slots = [];
  const spans = [];
  let incomplete = false;

  document.calendarInstance.getEvents().forEach((ev) => {
    if (ev.extendedProps.type === 'slot') {
      if (ev.extendedProps.available === null)
        incomplete = ev.start;

      slots.push({
        rspan_id: ev.extendedProps.rspan_id,
        start: ev.start,
        end: ev.end,
        available: ev.extendedProps.available,
      });
    } else if (ev.extendedProps.type === 'span') {
      spans.push({
        start: ev.start,
        end: ev.end,
      });
    }
  });

  if (incomplete) {
    alert('Please make sure to indicate your availability (yes/no) for all '
      + 'time slots shown in blue, by clicking them. '
      + `Incomplete slot: ${incomplete}`);
    return;
  }

  document.getElementById('calendarState').value = JSON.stringify({
    slots,
    spans,
  });

  document.getElementById('calendarForm').submit();
}

// eslint-disable-next-line no-unused-vars
function initialize(initialDate, nDays, events, hasSpans) {
  document.addEventListener(
    'DOMContentLoaded',
    () => {
      const calendarEl = document.getElementById('calendar');
      const calendar = new FullCalendar.Calendar(calendarEl, {
        // plugins: [timeGridPlugin],
        initialView: 'timeGridNDay',
        headerToolbar: {
          start: false,
          center: false,
          end: false,
        },
        views: {
          timeGridNDay: {
            type: 'timeGrid',
            duration: { days: nDays }
          }
        },
        dayHeaderFormat: { weekday: 'short', month: 'short', day: 'numeric', omitCommas: true },
        events,
        allDaySlot: false,
        initialDate,
        eventClick,
        selectable: hasSpans,
        select: calSelect,
      });
      calendar.render();

      document.calendarInstance = calendar;
      document.getElementById('submitButton').addEventListener('click', onSubmit);
    },
  );
}
