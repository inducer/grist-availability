const event_states = ["avr-unknown", "avr-confirmed", "avr-unavailable", "avr-drawn"];

function eventClick(info) {
  let ev = info.event;
  
}

function calSelect(info) {
  info.view.calendar.addEvent({
    start: info.start,
    end: info.end,
    editable: true});
}

function initialize(initialDate, events, hasSpans) {
  document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'timeGridWeek',
      events: events,
      allDaySlot: false,
      initialDate: initialDate,
      eventClick: eventClick,
      selectable: hasSpans,
      select: calSelect,
    });
    calendar.render();

    document.calendarInstance = calendar;
  });
}
