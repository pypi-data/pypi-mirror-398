"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["706"],{43102:function(e,t,a){a.d(t,{K:function(){return l},t:function(){return s}});var n,r,i=a(96196),o=e=>e,l=(0,i.qy)(n||(n=o`<svg height="24" viewBox="0 0 24 24" width="24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path></svg>`)),s=(0,i.qy)(r||(r=o`<svg height="24" viewBox="0 0 24 24" width="24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path></svg>`))},35769:function(e,t,a){a.a(e,(async function(e,t){try{var n=a(52588),r=a(33143),i=a(12402),o=e([n,r]);[n,r]=o.then?(await o)():o,(0,i.U)(n.$4,r.t),t()}catch(l){t(l)}}))},73095:function(e,t,a){a.d(t,{WA:function(){return c},mm:function(){return u}});var n,r,i,o,l,s=a(96196),d=e=>e,c=(0,s.AH)(n||(n=d`
button {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;

  position: relative;
  display: block;
  margin: 0;
  padding: 0;
  background: none; /** NOTE: IE11 fix */
  color: inherit;
  border: none;
  font: inherit;
  text-align: left;
  text-transform: inherit;
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
}
`)),u=((0,s.AH)(r||(r=d`
a {
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0);

  position: relative;
  display: inline-block;
  background: initial;
  color: inherit;
  font: inherit;
  text-transform: inherit;
  text-decoration: none;
  outline: none;
}
a:focus,
a:focus.page-selected {
  text-decoration: underline;
}
`)),(0,s.AH)(i||(i=d`
svg {
  display: block;
  min-width: var(--svg-icon-min-width, 24px);
  min-height: var(--svg-icon-min-height, 24px);
  fill: var(--svg-icon-fill, currentColor);
  pointer-events: none;
}
`)),(0,s.AH)(o||(o=d`[hidden] { display: none !important; }`)),(0,s.AH)(l||(l=d`
:host {
  display: block;

  /* --app-datepicker-width: 300px; */
  /* --app-datepicker-primary-color: #4285f4; */
  /* --app-datepicker-header-height: 80px; */
}

* {
  box-sizing: border-box;
}
`)))},52588:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{$4:function(){return p},$g:function(){return u},B0:function(){return o},Gf:function(){return d},YB:function(){return f},eB:function(){return c},tn:function(){return h}});a(28706),a(23792),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953);var r=a(22),i=e([r]);r=(i.then?(await i)():i)[0];var o=Intl&&Intl.DateTimeFormat,l=[38,33,36],s=[40,34,35],d=new Set([37].concat(l)),c=new Set([39].concat(s)),u=new Set([39].concat(l)),h=new Set([37].concat(s)),f=new Set([37,39].concat(l,s)),p="app-datepicker";n()}catch(y){n(y)}}))},33143:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{t:function(){return re}});var r=a(61397),i=a(50264),o=a(44734),l=a(56038),s=a(69683),d=a(6454),c=a(25460),u=(a(23792),a(62062),a(18111),a(61701),a(2892),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953),a(62826)),h=a(96196),f=a(77845),p=a(57378),y=a(94333),v=a(4937),m=a(13192),_=a(43102),b=a(73095),w=a(52588),g=a(58981),k=a(35676),D=a(82004),x=a(24571),T=a(97076),S=a(20335),C=a(50075),M=a(57445),F=a(46719),$=a(47614),U=a(60117),A=a(57407),N=a(447),W=a(84073),L=a(30622),E=a(49060),Y=a(93739),O=a(74745),q=a(46977),V=e([F,S,w,k]);[F,S,w,k]=V.then?(await V)():V;var P,Z,B,z,H,I,K,j,J,R,G,X,Q,ee,te,ae,ne=e=>e,re=function(e){function t(){var e;(0,o.A)(this,t),(e=(0,s.A)(this,t)).firstDayOfWeek=0,e.showWeekNumber=!1,e.weekNumberType="first-4-day-week",e.landscape=!1,e.locale=(0,F.f)(),e.disabledDays="",e.disabledDates="",e.weekLabel="Wk",e.inline=!1,e.dragRatio=.15,e._hasMin=!1,e._hasMax=!1,e._disabledDaysSet=new Set,e._disabledDatesSet=new Set,e._dx=-1/0,e._hasNativeWebAnimation="animate"in HTMLElement.prototype,e._updatingDateWithKey=!1;var a=(0,M.t)(),n=(0,S.G)(e.locale),r=(0,E.h)(a),i=(0,M.t)("2100-12-31");return e.value=r,e.startView="calendar",e._min=new Date(a),e._max=new Date(i),e._todayDate=a,e._maxDate=i,e._yearList=(0,Y.N)(a,i),e._selectedDate=new Date(a),e._focusedDate=new Date(a),e._formatters=n,e}return(0,d.A)(t,e),(0,l.A)(t,[{key:"startView",get:function(){return this._startView},set:function(e){var t=e||"calendar";if("calendar"===t||"yearList"===t){var a=this._startView;this._startView=t,this.requestUpdate("startView",a)}}},{key:"min",get:function(){return this._hasMin?(0,E.h)(this._min):""},set:function(e){var t=(0,M.t)(e),a=(0,U.v)(e,t);this._min=a?t:this._todayDate,this._hasMin=a,this.requestUpdate("min")}},{key:"max",get:function(){return this._hasMax?(0,E.h)(this._max):""},set:function(e){var t=(0,M.t)(e),a=(0,U.v)(e,t);this._max=a?t:this._maxDate,this._hasMax=a,this.requestUpdate("max")}},{key:"value",get:function(){return(0,E.h)(this._focusedDate)},set:function(e){var t=(0,M.t)(e),a=(0,U.v)(e,t)?t:this._todayDate;this._focusedDate=new Date(a),this._selectedDate=this._lastSelectedDate=new Date(a)}},{key:"disconnectedCallback",value:function(){(0,c.A)(t,"disconnectedCallback",this,3)([]),this._tracker&&(this._tracker.disconnect(),this._tracker=void 0)}},{key:"render",value:function(){this._formatters.locale!==this.locale&&(this._formatters=(0,S.G)(this.locale));var e="yearList"===this._startView?this._renderDatepickerYearList():this._renderDatepickerCalendar(),t=this.inline?null:(0,h.qy)(P||(P=ne`<div class="datepicker-header" part="header">${0}</div>`),this._renderHeaderSelectorButton());return(0,h.qy)(Z||(Z=ne`
    ${0}
    <div class="datepicker-body" part="body">${0}</div>
    `),t,(0,p.P)(e))}},{key:"firstUpdated",value:function(){var e;e="calendar"===this._startView?this.inline?this.shadowRoot.querySelector(".btn__month-selector"):this._buttonSelectorYear:this._yearViewListItem,(0,D.w)(this,"datepicker-first-updated",{firstFocusableElement:e,value:this.value})}},{key:"updated",value:(a=(0,i.A)((0,r.A)().m((function e(t){var a,n,o,l,s,d,c,u,h,f,p,y=this;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:a=this._startView,(t.has("min")||t.has("max"))&&(this._yearList=(0,Y.N)(this._min,this._max),"yearList"===a&&this.requestUpdate(),n=+this._min,o=+this._max,(0,T.u)(n,o)>864e5&&(l=+this._focusedDate,s=l,l<n&&(s=n),l>o&&(s=o),this.value=(0,E.h)(new Date(s)))),(t.has("_startView")||t.has("startView"))&&("yearList"===a&&(d=48*(this._selectedDate.getUTCFullYear()-this._min.getUTCFullYear()-2),(0,L.G)(this._yearViewFullList,{top:d,left:0})),"calendar"===a&&null==this._tracker&&(c=this.calendarsContainer,u=!1,h=!1,f=!1,c&&(p={down:()=>{f||(u=!0,this._dx=0)},move:(e,t)=>{if(!f&&u){var a=this._dx,n=a<0&&(0,$.n)(c,"has-max-date")||a>0&&(0,$.n)(c,"has-min-date");!n&&Math.abs(a)>0&&u&&(h=!0,c.style.transform=`translateX(${(0,A.b)(a)}px)`),this._dx=n?0:a+(e.x-t.x)}},up:function(){var e=(0,i.A)((0,r.A)().m((function e(t,a,n){var i,o,l,s;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(!u||!h){e.n=2;break}return i=y._dx,o=c.getBoundingClientRect().width/3,l=Math.abs(i)>Number(y.dragRatio)*o,s=l?(0,A.b)(o*(i<0?-1:1)):0,f=!0,e.n=1,(0,g.K)(c,{hasNativeWebAnimation:y._hasNativeWebAnimation,keyframes:[{transform:`translateX(${i}px)`},{transform:`translateX(${s}px)`}],options:{duration:350,easing:"cubic-bezier(0, 0, .4, 1)"}});case 1:l&&y._updateMonth(i<0?"next":"previous").handleEvent(),u=h=f=!1,y._dx=-1/0,c.removeAttribute("style"),(0,D.w)(y,"datepicker-animation-finished"),e.n=3;break;case 2:u&&(y._updateFocusedDate(n),u=h=!1,y._dx=-1/0);case 3:return e.a(2)}}),e)})));return function(t,a,n){return e.apply(this,arguments)}}()},this._tracker=new q.J(c,p))),t.get("_startView")&&"calendar"===a&&this._focusElement('[part="year-selector"]')),this._updatingDateWithKey&&(this._focusElement('[part="calendars"]:nth-of-type(2) .day--focused'),this._updatingDateWithKey=!1);case 1:return e.a(2)}}),e,this)}))),function(e){return a.apply(this,arguments)})},{key:"_focusElement",value:function(e){var t=this.shadowRoot.querySelector(e);t&&t.focus()}},{key:"_renderHeaderSelectorButton",value:function(){var e=this._formatters,t=e.yearFormat,a=e.dateFormat,n="calendar"===this.startView,r=this._focusedDate,i=a(r),o=t(r);return(0,h.qy)(B||(B=ne`
    <button
      class="${0}"
      type="button"
      part="year-selector"
      data-view="${0}"
      @click="${0}">${0}</button>

    <div class="datepicker-toolbar" part="toolbar">
      <button
        class="${0}"
        type="button"
        part="calendar-selector"
        data-view="${0}"
        @click="${0}">${0}</button>
    </div>
    `),(0,y.H)({"btn__year-selector":!0,selected:!n}),"yearList",this._updateView("yearList"),o,(0,y.H)({"btn__calendar-selector":!0,selected:n}),"calendar",this._updateView("calendar"),i)}},{key:"_renderDatepickerYearList",value:function(){var e=this._formatters.yearFormat,t=this._focusedDate.getUTCFullYear();return(0,h.qy)(z||(z=ne`
    <div class="datepicker-body__year-list-view" part="year-list-view">
      <div class="year-list-view__full-list" part="year-list" @click="${0}">
      ${0}</div>
    </div>
    `),this._updateYear,this._yearList.map((a=>(0,h.qy)(H||(H=ne`<button
        class="${0}"
        type="button"
        part="year"
        .year="${0}">${0}</button>`),(0,y.H)({"year-list-view__list-item":!0,"year--selected":t===a}),a,e((0,m.m)(a,0,1))))))}},{key:"_renderDatepickerCalendar",value:function(){var e=this._formatters,t=e.longMonthYearFormat,a=e.dayFormat,n=e.fullDateFormat,r=e.longWeekdayFormat,i=e.narrowWeekdayFormat,o=(0,W.S)(this.disabledDays,Number),l=(0,W.S)(this.disabledDates,M.t),s=this.showWeekNumber,d=this._focusedDate,c=this.firstDayOfWeek,u=(0,M.t)(),f=this._selectedDate,p=this._max,m=this._min,b=(0,C.n)({dayFormat:a,fullDateFormat:n,longWeekdayFormat:r,narrowWeekdayFormat:i,firstDayOfWeek:c,disabledDays:o,disabledDates:l,locale:this.locale,selectedDate:f,showWeekNumber:this.showWeekNumber,weekNumberType:this.weekNumberType,max:p,min:m,weekLabel:this.weekLabel}),w=b.calendars,g=b.disabledDaysSet,D=b.disabledDatesSet,x=b.weekdays,T=!w[0].calendar.length,S=!w[2].calendar.length,F=x.map((e=>(0,h.qy)(I||(I=ne`<th
        class="calendar-weekday"
        part="calendar-weekday"
        role="columnheader"
        aria-label="${0}"
      >
        <div class="weekday" part="weekday">${0}</div>
      </th>`),e.label,e.value))),$=(0,v.u)(w,(e=>e.key),((e,a)=>{var n=e.calendar;if(!n.length)return(0,h.qy)(K||(K=ne`<div class="calendar-container" part="calendar"></div>`));var r=`calendarcaption${a}`,i=n[1][1].fullDate,o=1===a,l=o&&!this._isInVisibleMonth(d,f)?(0,k.Y)({disabledDaysSet:g,disabledDatesSet:D,hasAltKey:!1,keyCode:36,focusedDate:d,selectedDate:f,minTime:+m,maxTime:+p}):d;return(0,h.qy)(j||(j=ne`
      <div class="calendar-container" part="calendar">
        <table class="calendar-table" part="table" role="grid" aria-labelledby="${0}">
          <caption id="${0}">
            <div class="calendar-label" part="label">${0}</div>
          </caption>

          <thead role="rowgroup">
            <tr class="calendar-weekdays" part="weekdays" role="row">${0}</tr>
          </thead>

          <tbody role="rowgroup">${0}</tbody>
        </table>
      </div>
      `),r,r,i?t(i):"",F,n.map((e=>(0,h.qy)(J||(J=ne`<tr role="row">${0}</tr>`),e.map(((e,t)=>{var a=e.disabled,n=e.fullDate,r=e.label,i=e.value;if(!n&&i&&s&&t<1)return(0,h.qy)(R||(R=ne`<th
                      class="full-calendar__day weekday-label"
                      part="calendar-day"
                      scope="row"
                      role="rowheader"
                      abbr="${0}"
                      aria-label="${0}"
                    >${0}</th>`),r,r,i);if(!i||!n)return(0,h.qy)(G||(G=ne`<td class="full-calendar__day day--empty" part="calendar-day"></td>`));var c=+new Date(n),f=+d===c,p=o&&l.getUTCDate()===Number(i);return(0,h.qy)(X||(X=ne`
                  <td
                    tabindex="${0}"
                    class="${0}"
                    part="calendar-day${0}"
                    role="gridcell"
                    aria-disabled="${0}"
                    aria-label="${0}"
                    aria-selected="${0}"
                    .fullDate="${0}"
                    .day="${0}"
                  >
                    <div
                      class="calendar-day"
                      part="day${0}"
                    >${0}</div>
                  </td>
                  `),p?"0":"-1",(0,y.H)({"full-calendar__day":!0,"day--disabled":a,"day--today":+u===c,"day--focused":!a&&f}),+u===c?" calendar-today":"",a?"true":"false",r,f?"true":"false",n,i,+u===c?" today":"",i)}))))))}));return this._disabledDatesSet=D,this._disabledDaysSet=g,(0,h.qy)(Q||(Q=ne`
    <div class="datepicker-body__calendar-view" part="calendar-view">
      <div class="calendar-view__month-selector" part="month-selectors">
        <div class="month-selector-container">${0}</div>

        <div class="month-selector-container">${0}</div>
      </div>

      <div
        class="${0}"
        part="calendars"
        @keyup="${0}"
      >${0}</div>
    </div>
    `),T?null:(0,h.qy)(ee||(ee=ne`
          <button
            class="btn__month-selector"
            type="button"
            part="month-selector"
            aria-label="Previous month"
            @click="${0}"
          >${0}</button>
        `),this._updateMonth("previous"),_.K),S?null:(0,h.qy)(te||(te=ne`
          <button
            class="btn__month-selector"
            type="button"
            part="month-selector"
            aria-label="Next month"
            @click="${0}"
          >${0}</button>
        `),this._updateMonth("next"),_.t),(0,y.H)({"calendars-container":!0,"has-min-date":T,"has-max-date":S}),this._updateFocusedDateWithKeyboard,$)}},{key:"_updateView",value:function(e){return(0,N.c)((()=>{"calendar"===e&&(this._selectedDate=this._lastSelectedDate=new Date((0,O.V)(this._focusedDate,this._min,this._max))),this._startView=e}))}},{key:"_updateMonth",value:function(e){return(0,N.c)((()=>{if(null==this.calendarsContainer)return this.updateComplete;var t=this._lastSelectedDate||this._selectedDate,a=this._min,n=this._max,r="previous"===e,i=(0,m.m)(t.getUTCFullYear(),t.getUTCMonth()+(r?-1:1),1),o=i.getUTCFullYear(),l=i.getUTCMonth(),s=a.getUTCFullYear(),d=a.getUTCMonth(),c=n.getUTCFullYear(),u=n.getUTCMonth();return o<s||o<=s&&l<d||(o>c||o>=c&&l>u)||(this._lastSelectedDate=i,this._selectedDate=this._lastSelectedDate),this.updateComplete}))}},{key:"_updateYear",value:function(e){var t=(0,x.z)(e,(e=>(0,$.n)(e,"year-list-view__list-item")));if(null!=t){var a=(0,O.V)(new Date(this._focusedDate).setUTCFullYear(+t.year),this._min,this._max);this._selectedDate=this._lastSelectedDate=new Date(a),this._focusedDate=new Date(a),this._startView="calendar"}}},{key:"_updateFocusedDate",value:function(e){var t=(0,x.z)(e,(e=>(0,$.n)(e,"full-calendar__day")));null==t||["day--empty","day--disabled","day--focused","weekday-label"].some((e=>(0,$.n)(t,e)))||(this._focusedDate=new Date(t.fullDate),(0,D.w)(this,"datepicker-value-updated",{isKeypress:!1,value:this.value}))}},{key:"_updateFocusedDateWithKeyboard",value:function(e){var t=e.keyCode;if(13===t||32===t)return(0,D.w)(this,"datepicker-value-updated",{keyCode:t,isKeypress:!0,value:this.value}),void(this._focusedDate=new Date(this._selectedDate));if(9!==t&&w.YB.has(t)){var a=this._selectedDate,n=(0,k.Y)({keyCode:t,selectedDate:a,disabledDatesSet:this._disabledDatesSet,disabledDaysSet:this._disabledDaysSet,focusedDate:this._focusedDate,hasAltKey:e.altKey,maxTime:+this._max,minTime:+this._min});this._isInVisibleMonth(n,a)||(this._selectedDate=this._lastSelectedDate=n),this._focusedDate=n,this._updatingDateWithKey=!0,(0,D.w)(this,"datepicker-value-updated",{keyCode:t,isKeypress:!0,value:this.value})}}},{key:"_isInVisibleMonth",value:function(e,t){var a=e.getUTCFullYear(),n=e.getUTCMonth(),r=t.getUTCFullYear(),i=t.getUTCMonth();return a===r&&n===i}},{key:"calendarsContainer",get:function(){return this.shadowRoot.querySelector(".calendars-container")}}]);var a}(h.WF);re.styles=[b.mm,b.WA,(0,h.AH)(ae||(ae=ne`
    :host {
      width: 312px;
      /** NOTE: Magic number as 16:9 aspect ratio does not look good */
      /* height: calc((var(--app-datepicker-width) / .66) - var(--app-datepicker-footer-height, 56px)); */
      background-color: var(--app-datepicker-bg-color, #fff);
      color: var(--app-datepicker-color, #000);
      border-radius:
        var(--app-datepicker-border-top-left-radius, 0)
        var(--app-datepicker-border-top-right-radius, 0)
        var(--app-datepicker-border-bottom-right-radius, 0)
        var(--app-datepicker-border-bottom-left-radius, 0);
      contain: content;
      overflow: hidden;
    }
    :host([landscape]) {
      display: flex;

      /** <iphone-5-landscape-width> - <standard-side-margin-width> */
      min-width: calc(568px - 16px * 2);
      width: calc(568px - 16px * 2);
    }

    .datepicker-header + .datepicker-body {
      border-top: 1px solid var(--app-datepicker-separator-color, #ddd);
    }
    :host([landscape]) > .datepicker-header + .datepicker-body {
      border-top: none;
      border-left: 1px solid var(--app-datepicker-separator-color, #ddd);
    }

    .datepicker-header {
      display: flex;
      flex-direction: column;
      align-items: flex-start;

      position: relative;
      padding: 16px 24px;
    }
    :host([landscape]) > .datepicker-header {
      /** :this.<one-liner-month-day-width> + :this.<side-padding-width> */
      min-width: calc(14ch + 24px * 2);
    }

    .btn__year-selector,
    .btn__calendar-selector {
      color: var(--app-datepicker-selector-color, rgba(0, 0, 0, .55));
      cursor: pointer;
      /* outline: none; */
    }
    .btn__year-selector.selected,
    .btn__calendar-selector.selected {
      color: currentColor;
    }

    /**
      * NOTE: IE11-only fix. This prevents formatted focused date from overflowing the container.
      */
    .datepicker-toolbar {
      width: 100%;
    }

    .btn__year-selector {
      font-size: 16px;
      font-weight: 700;
    }
    .btn__calendar-selector {
      font-size: 36px;
      font-weight: 700;
      line-height: 1;
    }

    .datepicker-body {
      position: relative;
      width: 100%;
      overflow: hidden;
    }

    .datepicker-body__calendar-view {
      min-height: 56px;
    }

    .calendar-view__month-selector {
      display: flex;
      align-items: center;

      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      padding: 0 8px;
      z-index: 1;
    }

    .month-selector-container {
      max-height: 56px;
      height: 100%;
    }
    .month-selector-container + .month-selector-container {
      margin: 0 0 0 auto;
    }

    .btn__month-selector {
      padding: calc((56px - 24px) / 2);
      /**
        * NOTE: button element contains no text, only SVG.
        * No extra height will incur with such setting.
        */
      line-height: 0;
    }
    .btn__month-selector > svg {
      fill: currentColor;
    }

    .calendars-container {
      display: flex;
      justify-content: center;

      position: relative;
      top: 0;
      left: calc(-100%);
      width: calc(100% * 3);
      transform: translateZ(0);
      will-change: transform;
      /**
        * NOTE: Required for Pointer Events API to work on touch devices.
        * Native \`pan-y\` action will be fired by the browsers since we only care about the
        * horizontal direction. This is great as vertical scrolling still works even when touch
        * event happens on a datepicker's calendar.
        */
      touch-action: pan-y;
      /* outline: none; */
    }

    .year-list-view__full-list {
      max-height: calc(48px * 7);
      overflow-y: auto;

      scrollbar-color: var(--app-datepicker-scrollbar-thumb-bg-color, rgba(0, 0, 0, .35)) rgba(0, 0, 0, 0);
      scrollbar-width: thin;
    }
    .year-list-view__full-list::-webkit-scrollbar {
      width: 8px;
      background-color: rgba(0, 0, 0, 0);
    }
    .year-list-view__full-list::-webkit-scrollbar-thumb {
      background-color: var(--app-datepicker-scrollbar-thumb-bg-color, rgba(0, 0, 0, .35));
      border-radius: 50px;
    }
    .year-list-view__full-list::-webkit-scrollbar-thumb:hover {
      background-color: var(--app-datepicker-scrollbar-thumb-hover-bg-color, rgba(0, 0, 0, .5));
    }

    .calendar-weekdays > th,
    .weekday-label {
      color: var(--app-datepicker-weekday-color, rgba(0, 0, 0, .55));
      font-weight: 400;
      transform: translateZ(0);
      will-change: transform;
    }

    .calendar-container,
    .calendar-label,
    .calendar-table {
      width: 100%;
    }

    .calendar-container {
      position: relative;
      padding: 0 16px 16px;
    }

    .calendar-table {
      -moz-user-select: none;
      -webkit-user-select: none;
      user-select: none;

      border-collapse: collapse;
      border-spacing: 0;
      text-align: center;
    }

    .calendar-label {
      display: flex;
      align-items: center;
      justify-content: center;

      height: 56px;
      font-weight: 500;
      text-align: center;
    }

    .calendar-weekday,
    .full-calendar__day {
      position: relative;
      width: calc(100% / 7);
      height: 0;
      padding: calc(100% / 7 / 2) 0;
      outline: none;
      text-align: center;
    }
    .full-calendar__day:not(.day--disabled):focus {
      outline: #000 dotted 1px;
      outline: -webkit-focus-ring-color auto 1px;
    }
    :host([showweeknumber]) .calendar-weekday,
    :host([showweeknumber]) .full-calendar__day {
      width: calc(100% / 8);
      padding-top: calc(100% / 8);
      padding-bottom: 0;
    }
    :host([showweeknumber]) th.weekday-label {
      padding: 0;
    }

    /**
      * NOTE: Interesting fact! That is ::after will trigger paint when dragging. This will trigger
      * layout and paint on **ONLY** affected nodes. This is much cheaper as compared to rendering
      * all :::after of all calendar day elements. When dragging the entire calendar container,
      * because of all layout and paint trigger on each and every ::after, this becomes a expensive
      * task for the browsers especially on low-end devices. Even though animating opacity is much
      * cheaper, the technique does not work here. Adding 'will-change' will further reduce overall
      * painting at the expense of memory consumption as many cells in a table has been promoted
      * a its own layer.
      */
    .full-calendar__day:not(.day--empty):not(.day--disabled):not(.weekday-label) {
      transform: translateZ(0);
      will-change: transform;
    }
    .full-calendar__day:not(.day--empty):not(.day--disabled):not(.weekday-label).day--focused::after,
    .full-calendar__day:not(.day--empty):not(.day--disabled):not(.day--focused):not(.weekday-label):hover::after {
      content: '';
      display: block;
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: var(--app-datepicker-accent-color, #1a73e8);
      border-radius: 50%;
      opacity: 0;
      pointer-events: none;
    }
    .full-calendar__day:not(.day--empty):not(.day--disabled):not(.weekday-label) {
      cursor: pointer;
      pointer-events: auto;
      -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
    }
    .full-calendar__day.day--focused:not(.day--empty):not(.day--disabled):not(.weekday-label)::after,
    .full-calendar__day.day--today.day--focused:not(.day--empty):not(.day--disabled):not(.weekday-label)::after {
      opacity: 1;
    }

    .calendar-weekday > .weekday,
    .full-calendar__day > .calendar-day {
      display: flex;
      align-items: center;
      justify-content: center;

      position: absolute;
      top: 5%;
      left: 5%;
      width: 90%;
      height: 90%;
      color: currentColor;
      font-size: 14px;
      pointer-events: none;
      z-index: 1;
    }
    .full-calendar__day.day--today {
      color: var(--app-datepicker-accent-color, #1a73e8);
    }
    .full-calendar__day.day--focused,
    .full-calendar__day.day--today.day--focused {
      color: var(--app-datepicker-focused-day-color, #fff);
    }
    .full-calendar__day.day--empty,
    .full-calendar__day.weekday-label,
    .full-calendar__day.day--disabled > .calendar-day {
      pointer-events: none;
    }
    .full-calendar__day.day--disabled:not(.day--today) {
      color: var(--app-datepicker-disabled-day-color, rgba(0, 0, 0, .55));
    }

    .year-list-view__list-item {
      position: relative;
      width: 100%;
      padding: 12px 16px;
      text-align: center;
      /** NOTE: Reduce paint when hovering and scrolling, but this increases memory usage */
      /* will-change: opacity; */
      /* outline: none; */
    }
    .year-list-view__list-item::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: var(--app-datepicker-focused-year-bg-color, #000);
      opacity: 0;
      pointer-events: none;
    }
    .year-list-view__list-item:focus::after {
      opacity: .05;
    }
    .year-list-view__list-item.year--selected {
      color: var(--app-datepicker-accent-color, #1a73e8);
      font-size: 24px;
      font-weight: 500;
    }

    @media (any-hover: hover) {
      .btn__month-selector:hover,
      .year-list-view__list-item:hover {
        cursor: pointer;
      }
      .full-calendar__day:not(.day--empty):not(.day--disabled):not(.day--focused):not(.weekday-label):hover::after {
        opacity: .15;
      }
      .year-list-view__list-item:hover::after {
        opacity: .05;
      }
    }

    @supports (background: -webkit-canvas(squares)) {
      .calendar-container {
        padding: 56px 16px 16px;
      }

      table > caption {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translate3d(-50%, 0, 0);
        will-change: transform;
      }
    }
    `))],(0,u.__decorate)([(0,f.MZ)({type:Number,reflect:!0})],re.prototype,"firstDayOfWeek",void 0),(0,u.__decorate)([(0,f.MZ)({type:Boolean,reflect:!0})],re.prototype,"showWeekNumber",void 0),(0,u.__decorate)([(0,f.MZ)({type:String,reflect:!0})],re.prototype,"weekNumberType",void 0),(0,u.__decorate)([(0,f.MZ)({type:Boolean,reflect:!0})],re.prototype,"landscape",void 0),(0,u.__decorate)([(0,f.MZ)({type:String,reflect:!0})],re.prototype,"startView",null),(0,u.__decorate)([(0,f.MZ)({type:String,reflect:!0})],re.prototype,"min",null),(0,u.__decorate)([(0,f.MZ)({type:String,reflect:!0})],re.prototype,"max",null),(0,u.__decorate)([(0,f.MZ)({type:String})],re.prototype,"value",null),(0,u.__decorate)([(0,f.MZ)({type:String})],re.prototype,"locale",void 0),(0,u.__decorate)([(0,f.MZ)({type:String})],re.prototype,"disabledDays",void 0),(0,u.__decorate)([(0,f.MZ)({type:String})],re.prototype,"disabledDates",void 0),(0,u.__decorate)([(0,f.MZ)({type:String})],re.prototype,"weekLabel",void 0),(0,u.__decorate)([(0,f.MZ)({type:Boolean})],re.prototype,"inline",void 0),(0,u.__decorate)([(0,f.MZ)({type:Number})],re.prototype,"dragRatio",void 0),(0,u.__decorate)([(0,f.MZ)({type:Date,attribute:!1})],re.prototype,"_selectedDate",void 0),(0,u.__decorate)([(0,f.MZ)({type:Date,attribute:!1})],re.prototype,"_focusedDate",void 0),(0,u.__decorate)([(0,f.MZ)({type:String,attribute:!1})],re.prototype,"_startView",void 0),(0,u.__decorate)([(0,f.P)(".year-list-view__full-list")],re.prototype,"_yearViewFullList",void 0),(0,u.__decorate)([(0,f.P)(".btn__year-selector")],re.prototype,"_buttonSelectorYear",void 0),(0,u.__decorate)([(0,f.P)(".year-list-view__list-item")],re.prototype,"_yearViewListItem",void 0),(0,u.__decorate)([(0,f.Ls)({passive:!0})],re.prototype,"_updateYear",null),(0,u.__decorate)([(0,f.Ls)({passive:!0})],re.prototype,"_updateFocusedDateWithKeyboard",null),n()}catch(ie){n(ie)}}))},58981:function(e,t,a){a.d(t,{K:function(){return o}});var n=a(61397),r=a(78261),i=a(50264);a(18111),a(7588),a(26099),a(3362),a(23500);function o(e,t){return l.apply(this,arguments)}function l(){return(l=(0,i.A)((0,n.A)().m((function e(t,a){var i,o,l,s,d,c,u;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:if(o=(i=a||{}).hasNativeWebAnimation,l=void 0!==o&&o,s=i.keyframes,d=void 0===s?[]:s,c=i.options,u=void 0===c?{duration:100}:c,Array.isArray(d)&&d.length){e.n=1;break}return e.a(2);case 1:return e.a(2,new Promise((e=>{if(l){t.animate(d,u).onfinish=()=>e()}else{var a=d||[],n=(0,r.A)(a,2)[1],i=()=>{t.removeEventListener("transitionend",i),e()};t.addEventListener("transitionend",i),t.style.transitionDuration=`${u.duration}ms`,u.easing&&(t.style.transitionTimingFunction=u.easing),Object.keys(n).forEach((e=>{e&&(t.style[e]=n[e])}))}})))}}),e)})))).apply(this,arguments)}},35676:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{Y:function(){return d}});var r=a(13192),i=a(52588),o=a(61881),l=e([i,o]);function d(e){var t=e.hasAltKey,a=e.keyCode,n=e.focusedDate,l=e.selectedDate,s=e.disabledDaysSet,d=e.disabledDatesSet,c=e.minTime,u=e.maxTime,h=n.getUTCFullYear(),f=n.getUTCMonth(),p=n.getUTCDate(),y=+n,v=l.getUTCFullYear(),m=l.getUTCMonth(),_=h,b=f,w=p,g=!0;switch((m!==f||v!==h)&&(_=v,b=m,w=1,g=34===a||33===a||35===a),g){case y===c&&i.Gf.has(a):case y===u&&i.eB.has(a):break;case 38===a:w-=7;break;case 40===a:w+=7;break;case 37===a:w-=1;break;case 39===a:w+=1;break;case 34===a:t?_+=1:b+=1;break;case 33===a:t?_-=1:b-=1;break;case 35===a:b+=1,w=0;break;default:w=1}if(34===a||33===a){var k=(0,r.m)(_,b+1,0).getUTCDate();w>k&&(w=k)}return(0,o.i)({keyCode:a,maxTime:u,minTime:c,disabledDaysSet:s,disabledDatesSet:d,focusedDate:(0,r.m)(_,b,w)})}[i,o]=l.then?(await l)():l,n()}catch(s){n(s)}}))},12402:function(e,t,a){function n(e,t){window.customElements&&!window.customElements.get(e)&&window.customElements.define(e,t)}a.d(t,{U:function(){return n}})},82004:function(e,t,a){function n(e,t,a){return e.dispatchEvent(new CustomEvent(t,{detail:a,bubbles:!0,composed:!0}))}a.d(t,{w:function(){return n}})},24571:function(e,t,a){a.d(t,{z:function(){return n}});a(50113),a(18111),a(20116),a(26099);function n(e,t){return e.composedPath().find((e=>e instanceof HTMLElement&&t(e)))}},97076:function(e,t,a){function n(e,t){return+t-+e}a.d(t,{u:function(){return n}})},20335:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{G:function(){return s}});var r=a(36886),i=a(52588),o=e([i]);function s(e){var t=(0,i.B0)(e,{timeZone:"UTC",weekday:"short",month:"short",day:"numeric"}),a=(0,i.B0)(e,{timeZone:"UTC",day:"numeric"}),n=(0,i.B0)(e,{timeZone:"UTC",year:"numeric",month:"short",day:"numeric"}),o=(0,i.B0)(e,{timeZone:"UTC",year:"numeric",month:"long"}),l=(0,i.B0)(e,{timeZone:"UTC",weekday:"long"}),s=(0,i.B0)(e,{timeZone:"UTC",weekday:"narrow"}),d=(0,i.B0)(e,{timeZone:"UTC",year:"numeric"});return{locale:e,dateFormat:(0,r.f)(t),dayFormat:(0,r.f)(a),fullDateFormat:(0,r.f)(n),longMonthYearFormat:(0,r.f)(o),longWeekdayFormat:(0,r.f)(l),narrowWeekdayFormat:(0,r.f)(s),yearFormat:(0,r.f)(d)}}i=(o.then?(await o)():o)[0],n()}catch(l){n(l)}}))},50075:function(e,t,a){a.d(t,{n:function(){return h}});var n=a(20054),r=a(31432),i=(a(2008),a(23792),a(62062),a(44114),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953),a(23418),a(72712),a(18111),a(18237),a(13192));a(52675),a(89463),a(16280),a(34782),a(27495),a(90906),a(38781);function o(e,t){(null==t||t>e.length)&&(t=e.length);for(var a=0,n=Array(t);a<t;a++)n[a]=e[a];return n}function l(e,t){var a="undefined"!=typeof Symbol&&e[Symbol.iterator]||e["@@iterator"];if(!a){if(Array.isArray(e)||(a=function(e,t){if(e){if("string"==typeof e)return o(e,t);var a={}.toString.call(e).slice(8,-1);return"Object"===a&&e.constructor&&(a=e.constructor.name),"Map"===a||"Set"===a?Array.from(e):"Arguments"===a||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(a)?o(e,t):void 0}}(e))||t&&e&&"number"==typeof e.length){a&&(e=a);var n=0,r=function(){};return{s:r,n:function(){return n>=e.length?{done:!0}:{done:!1,value:e[n++]}},e:function(e){throw e},f:r}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var i,l=!0,s=!1;return{s:function(){a=a.call(e)},n:function(){var e=a.next();return l=e.done,e},e:function(e){s=!0,i=e},f:function(){try{l||null==a.return||a.return()}finally{if(s)throw i}}}}a(28706),a(61701);function s(e,t){var a=function(e,t){var a=t.getUTCFullYear(),n=t.getUTCMonth(),r=t.getUTCDate(),o=t.getUTCDay(),l=o;return"first-4-day-week"===e&&(l=3),"first-day-of-year"===e&&(l=6),"first-full-week"===e&&(l=0),(0,i.m)(a,n,r-o+l)}(e,t),n=(0,i.m)(a.getUTCFullYear(),0,1),r=1+(+a-+n)/864e5;return Math.ceil(r/7)}function d(e){return e>=0&&e<7?Math.abs(e):((e<0?7*Math.ceil(Math.abs(e)):0)+e)%7}function c(e,t,a){var n=d(e-t);return a?1+n:n}a(36886);var u=["disabledDatesSet","disabledDaysSet"];function h(e){var t,a=e.dayFormat,o=e.fullDateFormat,h=e.locale,f=e.longWeekdayFormat,p=e.narrowWeekdayFormat,y=e.selectedDate,v=e.disabledDates,m=e.disabledDays,_=e.firstDayOfWeek,b=e.max,w=e.min,g=e.showWeekNumber,k=e.weekLabel,D=e.weekNumberType,x=null==w?Number.MIN_SAFE_INTEGER:+w,T=null==b?Number.MAX_SAFE_INTEGER:+b,S=function(e){var t=e||{},a=t.firstDayOfWeek,n=void 0===a?0:a,r=t.showWeekNumber,o=void 0!==r&&r,l=t.weekLabel,s=t.longWeekdayFormat,d=t.narrowWeekdayFormat,c=1+(n+(n<0?7:0))%7,u=l||"Wk",h=o?[{label:"Wk"===u?"Week":u,value:u}]:[];return Array.from(Array(7)).reduce(((e,t,a)=>{var n=(0,i.m)(2017,0,c+a);return e.push({label:s(n),value:d(n)}),e}),h)}({longWeekdayFormat:f,narrowWeekdayFormat:p,firstDayOfWeek:_,showWeekNumber:g,weekLabel:k}),C=e=>[h,e.toJSON(),null==v?void 0:v.join("_"),null==m?void 0:m.join("_"),_,null==b?void 0:b.toJSON(),null==w?void 0:w.toJSON(),g,k,D].filter(Boolean).join(":"),M=y.getUTCFullYear(),F=y.getUTCMonth(),$=[-1,0,1].map((e=>{var t=(0,i.m)(M,F+e,1),n=+(0,i.m)(M,F+e+1,0),r=C(t);if(n<x||+t>T)return{key:r,calendar:[],disabledDatesSet:new Set,disabledDaysSet:new Set};var u=function(e){for(var t=e||{},a=t.date,n=t.dayFormat,r=t.disabledDates,o=void 0===r?[]:r,u=t.disabledDays,h=void 0===u?[]:u,f=t.firstDayOfWeek,p=void 0===f?0:f,y=t.fullDateFormat,v=t.locale,m=void 0===v?"en-US":v,_=t.max,b=t.min,w=t.showWeekNumber,g=void 0!==w&&w,k=t.weekLabel,D=void 0===k?"Week":k,x=t.weekNumberType,T=void 0===x?"first-4-day-week":x,S=d(p),C=a.getUTCFullYear(),M=a.getUTCMonth(),F=(0,i.m)(C,M,1),$=new Set(h.map((e=>c(e,S,g)))),U=new Set(o.map((e=>+e))),A=[F.toJSON(),S,m,null==_?"":_.toJSON(),null==b?"":b.toJSON(),Array.from($).join(","),Array.from(U).join(","),T].filter(Boolean).join(":"),N=c(F.getUTCDay(),S,g),W=null==b?+new Date("2000-01-01"):+b,L=null==_?+new Date("2100-12-31"):+_,E=g?8:7,Y=(0,i.m)(C,1+M,0).getUTCDate(),O=[],q=[],V=!1,P=1,Z=0,B=[0,1,2,3,4,5];Z<B.length;Z++){var z,H=B[Z],I=l([0,1,2,3,4,5,6].concat(7===E?[]:[7]));try{for(I.s();!(z=I.n()).done;){var K=z.value,j=K+H*E;if(V||!g||0!==K)if(V||j<N)q.push({fullDate:null,label:"",value:"",key:`${A}:${j}`,disabled:!0});else{var J=(0,i.m)(C,M,P),R=+J,G=$.has(K)||U.has(R)||R<W||R>L;G&&U.add(R),q.push({fullDate:J,label:y(J),value:n(J),key:`${A}:${J.toJSON()}`,disabled:G}),(P+=1)>Y&&(V=!0)}else{var X=H<1?S:0,Q=s(T,(0,i.m)(C,M,P-X)),ee=`${D} ${Q}`;q.push({fullDate:null,label:ee,value:`${Q}`,key:`${A}:${ee}`,disabled:!0})}}}catch(te){I.e(te)}finally{I.f()}O.push(q),q=[]}return{disabledDatesSet:U,calendar:O,disabledDaysSet:new Set(h.map((e=>d(e)))),key:A}}({dayFormat:a,fullDateFormat:o,locale:h,disabledDates:v,disabledDays:m,firstDayOfWeek:_,max:b,min:w,showWeekNumber:g,weekLabel:k,weekNumberType:D,date:t});return Object.assign(Object.assign({},u),{},{key:r})})),U=[],A=new Set,N=new Set,W=(0,r.A)($);try{for(W.s();!(t=W.n()).done;){var L=t.value,E=L.disabledDatesSet,Y=L.disabledDaysSet,O=(0,n.A)(L,u);if(O.calendar.length>0){if(Y.size>0){var q,V=(0,r.A)(Y);try{for(V.s();!(q=V.n()).done;){var P=q.value;N.add(P)}}catch(H){V.e(H)}finally{V.f()}}if(E.size>0){var Z,B=(0,r.A)(E);try{for(B.s();!(Z=B.n()).done;){var z=Z.value;A.add(z)}}catch(H){B.e(H)}finally{B.f()}}}U.push(O)}}catch(H){W.e(H)}finally{W.f()}return{calendars:U,weekdays:S,disabledDatesSet:A,disabledDaysSet:N,key:C(y)}}},57445:function(e,t,a){a.d(t,{t:function(){return r}});a(27495),a(90906);var n=a(13192);function r(e){var t=null==e?new Date:new Date(e),a="string"==typeof e&&(/^\d{4}-\d{2}-\d{2}$/i.test(e)||/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}(Z|\+00:00|-00:00)$/i.test(e)),r="number"==typeof e&&e>0&&isFinite(e),i=t.getFullYear(),o=t.getMonth(),l=t.getDate();return(a||r)&&(i=t.getUTCFullYear(),o=t.getUTCMonth(),l=t.getUTCDate()),(0,n.m)(i,o,l)}},46719:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{f:function(){return l}});var r=a(52588),i=e([r]);function l(){return r.B0&&(0,r.B0)().resolvedOptions&&(0,r.B0)().resolvedOptions().locale||"en-US"}r=(i.then?(await i)():i)[0],n()}catch(o){n(o)}}))},61881:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{i:function(){return d}});var r=a(13192),i=a(52588),o=a(97076),l=e([i]);function d(e){var t=e.keyCode,a=e.disabledDaysSet,n=e.disabledDatesSet,l=e.focusedDate,s=e.maxTime,d=e.minTime,c=+l,u=c<d,h=c>s;if((0,o.u)(d,s)<864e5)return l;var f=u||h||a.has(l.getUTCDay())||n.has(c);if(!f)return l;for(var p=0,y=u===h?l:new Date(u?d-864e5:864e5+s),v=y.getUTCFullYear(),m=y.getUTCMonth(),_=y.getUTCDate();f;)(u||!h&&i.$g.has(t))&&(_+=1),(h||!u&&i.tn.has(t))&&(_-=1),p=+(y=(0,r.m)(v,m,_)),u||(u=p<d)&&(p=+(y=new Date(d)),_=y.getUTCDate()),h||(h=p>s)&&(p=+(y=new Date(s)),_=y.getUTCDate()),f=a.has(y.getUTCDay())||n.has(p);return y}i=(l.then?(await l)():l)[0],n()}catch(s){n(s)}}))},47614:function(e,t,a){function n(e,t){return e.classList.contains(t)}a.d(t,{n:function(){return n}})},60117:function(e,t,a){function n(e,t){return!(null==e||!(t instanceof Date)||isNaN(+t))}a.d(t,{v:function(){return n}})},57407:function(e,t,a){function n(e){return e-Math.floor(e)>0?+e.toFixed(3):e}a.d(t,{b:function(){return n}})},447:function(e,t,a){function n(e){return{passive:!0,handleEvent:e}}a.d(t,{c:function(){return n}})},84073:function(e,t,a){a.d(t,{S:function(){return n}});a(62062),a(18111),a(61701),a(26099),a(27495),a(90744);function n(e,t){var a="string"==typeof e&&e.length>0?e.split(/,\s*/i):[];return a.length?"function"==typeof t?a.map(t):a:[]}},30622:function(e,t,a){function n(e,t){if(null==e.scrollTo){var a=t||{},n=a.top,r=a.left;e.scrollTop=n||0,e.scrollLeft=r||0}else e.scrollTo(t)}a.d(t,{G:function(){return n}})},49060:function(e,t,a){a.d(t,{h:function(){return n}});a(27495),a(25440);function n(e){if(e instanceof Date&&!isNaN(+e)){var t=e.toJSON();return null==t?"":t.replace(/^(.+)T.+/i,"$1")}return""}},93739:function(e,t,a){a.d(t,{N:function(){return r}});a(23418);var n=a(97076);function r(e,t){if((0,n.u)(e,t)<864e5)return[];var a=e.getUTCFullYear();return Array.from(Array(t.getUTCFullYear()-a+1),((e,t)=>t+a))}},74745:function(e,t,a){function n(e,t,a){var n="number"==typeof e?e:+e,r=+t,i=+a;return n<r?r:n>i?i:e}a.d(t,{V:function(){return n}})},46977:function(e,t,a){a.d(t,{J:function(){return d}});var n=a(44734),r=a(56038),i=(a(50113),a(23418),a(18111),a(20116),a(26099),a(12130));function o(e){var t=e.clientX,a=e.clientY,n=e.pageX,r=e.pageY,i=Math.max(n,t),o=Math.max(r,a),l=e.identifier||e.pointerId;return{x:i,y:o,id:null==l?0:l}}function l(e,t){var a=t.changedTouches;if(null==a)return{newPointer:o(t),oldPointer:e};var n=Array.from(a,(e=>o(e)));return{newPointer:null==e?n[0]:n.find((t=>t.id===e.id)),oldPointer:e}}function s(e,t,a){e.addEventListener(t,a,!!i.QQ&&{passive:!0})}var d=function(){return(0,r.A)((function e(t,a){(0,n.A)(this,e),this._element=t,this._startPointer=null;var r=a.down,i=a.move,o=a.up;this._down=this._onDown(r),this._move=this._onMove(i),this._up=this._onUp(o),t&&t.addEventListener&&(t.addEventListener("mousedown",this._down),s(t,"touchstart",this._down),s(t,"touchmove",this._move),s(t,"touchend",this._up))}),[{key:"disconnect",value:function(){var e=this._element;e&&e.removeEventListener&&(e.removeEventListener("mousedown",this._down),e.removeEventListener("touchstart",this._down),e.removeEventListener("touchmove",this._move),e.removeEventListener("touchend",this._up))}},{key:"_onDown",value:function(e){return t=>{t instanceof MouseEvent&&(this._element.addEventListener("mousemove",this._move),this._element.addEventListener("mouseup",this._up),this._element.addEventListener("mouseleave",this._up));var a=l(this._startPointer,t).newPointer;e(a,t),this._startPointer=a}}},{key:"_onMove",value:function(e){return t=>{this._updatePointers(e,t)}}},{key:"_onUp",value:function(e){return t=>{this._updatePointers(e,t,!0)}}},{key:"_updatePointers",value:function(e,t,a){a&&t instanceof MouseEvent&&(this._element.removeEventListener("mousemove",this._move),this._element.removeEventListener("mouseup",this._up),this._element.removeEventListener("mouseleave",this._up));var n=l(this._startPointer,t),r=n.newPointer;e(r,n.oldPointer,t),this._startPointer=a?null:r}}])}()},2045:function(e,t,a){a.d(t,{q:function(){return r}});var n={};function r(){return n}},74816:function(e,t,a){a.d(t,{x:function(){return r}});a(50113),a(62062),a(18111),a(20116),a(61701),a(26099);var n=a(73420);function r(e){for(var t=arguments.length,a=new Array(t>1?t-1:0),r=1;r<t;r++)a[r-1]=arguments[r];var i=n.w.bind(null,e||a.find((e=>"object"==typeof e)));return a.map(i)}},9160:function(e,t,a){a.d(t,{Cg:function(){return i},_P:function(){return l},my:function(){return n},s0:function(){return o},w4:function(){return r}});Math.pow(10,8);var n=6048e5,r=864e5,i=6e4,o=36e5,l=Symbol.for("constructDateFrom")},73420:function(e,t,a){a.d(t,{w:function(){return r}});var n=a(9160);function r(e,t){return"function"==typeof e?e(t):e&&"object"==typeof e&&n._P in e?e[n._P](t):e instanceof Date?new e.constructor(t):new Date(t)}},3952:function(e,t,a){a.d(t,{m:function(){return d}});var n=a(78261),r=a(83504);function i(e){var t=(0,r.a)(e),a=new Date(Date.UTC(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds(),t.getMilliseconds()));return a.setUTCFullYear(t.getFullYear()),+e-+a}var o=a(74816),l=a(9160),s=a(35932);function d(e,t,a){var r=(0,o.x)(null==a?void 0:a.in,e,t),d=(0,n.A)(r,2),c=d[0],u=d[1],h=(0,s.o)(c),f=(0,s.o)(u),p=+h-i(h),y=+f-i(f);return Math.round((p-y)/l.w4)}},35932:function(e,t,a){a.d(t,{o:function(){return r}});var n=a(83504);function r(e,t){var a=(0,n.a)(e,null==t?void 0:t.in);return a.setHours(0,0,0,0),a}},52640:function(e,t,a){a.d(t,{k:function(){return i}});var n=a(2045),r=a(83504);function i(e,t){var a,i,o,l,s,d,c=(0,n.q)(),u=null!==(a=null!==(i=null!==(o=null!==(l=null==t?void 0:t.weekStartsOn)&&void 0!==l?l:null==t||null===(s=t.locale)||void 0===s||null===(s=s.options)||void 0===s?void 0:s.weekStartsOn)&&void 0!==o?o:c.weekStartsOn)&&void 0!==i?i:null===(d=c.locale)||void 0===d||null===(d=d.options)||void 0===d?void 0:d.weekStartsOn)&&void 0!==a?a:0,h=(0,r.a)(e,null==t?void 0:t.in),f=h.getDay(),p=(f<u?7:0)+f-u;return h.setDate(h.getDate()-p),h.setHours(0,0,0,0),h}},83504:function(e,t,a){a.d(t,{a:function(){return r}});var n=a(73420);function r(e,t){return(0,n.w)(t||e,e)}},57378:function(e,t,a){a.d(t,{P:function(){return h}});var n=a(78261),r=a(44734),i=a(56038),o=a(69683),l=a(6454),s=(a(23792),a(26099),a(73772),a(62953),a(4610)),d=a(42017),c=a(63937),u=e=>(0,c.ps)(e)?e._$litType$.h:e.strings,h=(0,d.u$)(function(e){function t(e){var a;return(0,r.A)(this,t),(a=(0,o.A)(this,t,[e])).et=new WeakMap,a}return(0,l.A)(t,e),(0,i.A)(t,[{key:"render",value:function(e){return[e]}},{key:"update",value:function(e,t){var a=(0,n.A)(t,1)[0],r=(0,c.qb)(this.it)?u(this.it):null,i=(0,c.qb)(a)?u(a):null;if(null!==r&&(null===i||r!==i)){var o=(0,c.cN)(e).pop(),l=this.et.get(r);if(void 0===l){var d=document.createDocumentFragment();(l=(0,s.XX)(s.s6,d)).setConnected(!1),this.et.set(r,l)}(0,c.mY)(l,[o]),(0,c.Dx)(l,void 0,o)}if(null!==i){if(null===r||r!==i){var h=this.et.get(i);if(void 0!==h){var f=(0,c.cN)(h).pop();(0,c.Jz)(e),(0,c.Dx)(e,void 0,f),(0,c.mY)(e,[f])}}this.it=a}else this.it=void 0;return this.render(a)}}])}(d.WL))},36886:function(e,t,a){a.d(t,{f:function(){return n}});a(27495),a(25440);function n(e){return t=>e.format(t).replace(/\u200e/gi,"")}},13192:function(e,t,a){function n(e,t,a){return new Date(Date.UTC(e,t,a))}a.d(t,{m:function(){return n}})}}]);
//# sourceMappingURL=706.7a9725694909faa3.js.map