/*! For license information please see 706.ab2f8ffb3c13502e.js.LICENSE.txt */
export const __webpack_id__="706";export const __webpack_ids__=["706"];export const __webpack_modules__={43102:function(e,t,a){a.d(t,{K:()=>i,t:()=>r});var n=a(96196);const i=n.qy`<svg height="24" viewBox="0 0 24 24" width="24"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path></svg>`,r=n.qy`<svg height="24" viewBox="0 0 24 24" width="24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path></svg>`},35769:function(e,t,a){a.a(e,(async function(e,t){try{var n=a(52588),i=a(33143),r=a(12402),o=e([n,i]);[n,i]=o.then?(await o)():o,(0,r.U)(n.$4,i.t),t()}catch(s){t(s)}}))},73095:function(e,t,a){a.d(t,{WA:()=>i,mm:()=>r});var n=a(96196);const i=n.AH`
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
`,r=(n.AH`
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
`,n.AH`
svg {
  display: block;
  min-width: var(--svg-icon-min-width, 24px);
  min-height: var(--svg-icon-min-height, 24px);
  fill: var(--svg-icon-fill, currentColor);
  pointer-events: none;
}
`,n.AH`[hidden] { display: none !important; }`,n.AH`
:host {
  display: block;

  /* --app-datepicker-width: 300px; */
  /* --app-datepicker-primary-color: #4285f4; */
  /* --app-datepicker-header-height: 80px; */
}

* {
  box-sizing: border-box;
}
`)},52588:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{$4:()=>y,$g:()=>u,B0:()=>o,Gf:()=>d,YB:()=>p,eB:()=>c,tn:()=>h});var i=a(22),r=e([i]);i=(r.then?(await r)():r)[0];const o=Intl&&Intl.DateTimeFormat,s=[38,33,36],l=[40,34,35],d=new Set([37,...s]),c=new Set([39,...l]),u=new Set([39,...s]),h=new Set([37,...l]),p=new Set([37,39,...s,...l]),y="app-datepicker";n()}catch(o){n(o)}}))},33143:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{t:()=>L});var i=a(62826),r=a(96196),o=a(77845),s=a(57378),l=a(94333),d=a(4937),c=a(13192),u=a(43102),h=a(73095),p=a(52588),y=a(58981),f=a(35676),m=a(82004),_=a(24571),b=a(97076),w=a(20335),v=a(86530),g=a(57445),k=a(46719),D=a(47614),x=a(60117),T=a(57407),S=a(447),C=a(84073),F=a(30622),M=a(49060),$=a(93739),U=a(74745),N=a(46977),W=e([p,f,k,w]);[p,f,k,w]=W.then?(await W)():W;class L extends r.WF{get startView(){return this._startView}set startView(e){const t=e||"calendar";if("calendar"!==t&&"yearList"!==t)return;const a=this._startView;this._startView=t,this.requestUpdate("startView",a)}get min(){return this._hasMin?(0,M.h)(this._min):""}set min(e){const t=(0,g.t)(e),a=(0,x.v)(e,t);this._min=a?t:this._todayDate,this._hasMin=a,this.requestUpdate("min")}get max(){return this._hasMax?(0,M.h)(this._max):""}set max(e){const t=(0,g.t)(e),a=(0,x.v)(e,t);this._max=a?t:this._maxDate,this._hasMax=a,this.requestUpdate("max")}get value(){return(0,M.h)(this._focusedDate)}set value(e){const t=(0,g.t)(e),a=(0,x.v)(e,t)?t:this._todayDate;this._focusedDate=new Date(a),this._selectedDate=this._lastSelectedDate=new Date(a)}disconnectedCallback(){super.disconnectedCallback(),this._tracker&&(this._tracker.disconnect(),this._tracker=void 0)}render(){this._formatters.locale!==this.locale&&(this._formatters=(0,w.G)(this.locale));const e="yearList"===this._startView?this._renderDatepickerYearList():this._renderDatepickerCalendar(),t=this.inline?null:r.qy`<div class="datepicker-header" part="header">${this._renderHeaderSelectorButton()}</div>`;return r.qy`
    ${t}
    <div class="datepicker-body" part="body">${(0,s.P)(e)}</div>
    `}firstUpdated(){let e;e="calendar"===this._startView?this.inline?this.shadowRoot.querySelector(".btn__month-selector"):this._buttonSelectorYear:this._yearViewListItem,(0,m.w)(this,"datepicker-first-updated",{firstFocusableElement:e,value:this.value})}async updated(e){const t=this._startView;if(e.has("min")||e.has("max")){this._yearList=(0,$.N)(this._min,this._max),"yearList"===t&&this.requestUpdate();const e=+this._min,a=+this._max;if((0,b.u)(e,a)>864e5){const t=+this._focusedDate;let n=t;t<e&&(n=e),t>a&&(n=a),this.value=(0,M.h)(new Date(n))}}if(e.has("_startView")||e.has("startView")){if("yearList"===t){const e=48*(this._selectedDate.getUTCFullYear()-this._min.getUTCFullYear()-2);(0,F.G)(this._yearViewFullList,{top:e,left:0})}if("calendar"===t&&null==this._tracker){const e=this.calendarsContainer;let t=!1,a=!1,n=!1;if(e){const i={down:()=>{n||(t=!0,this._dx=0)},move:(i,r)=>{if(n||!t)return;const o=this._dx,s=o<0&&(0,D.n)(e,"has-max-date")||o>0&&(0,D.n)(e,"has-min-date");!s&&Math.abs(o)>0&&t&&(a=!0,e.style.transform=`translateX(${(0,T.b)(o)}px)`),this._dx=s?0:o+(i.x-r.x)},up:async(i,r,o)=>{if(t&&a){const i=this._dx,r=e.getBoundingClientRect().width/3,o=Math.abs(i)>Number(this.dragRatio)*r,s=350,l="cubic-bezier(0, 0, .4, 1)",d=o?(0,T.b)(r*(i<0?-1:1)):0;n=!0,await(0,y.K)(e,{hasNativeWebAnimation:this._hasNativeWebAnimation,keyframes:[{transform:`translateX(${i}px)`},{transform:`translateX(${d}px)`}],options:{duration:s,easing:l}}),o&&this._updateMonth(i<0?"next":"previous").handleEvent(),t=a=n=!1,this._dx=-1/0,e.removeAttribute("style"),(0,m.w)(this,"datepicker-animation-finished")}else t&&(this._updateFocusedDate(o),t=a=!1,this._dx=-1/0)}};this._tracker=new N.J(e,i)}}e.get("_startView")&&"calendar"===t&&this._focusElement('[part="year-selector"]')}this._updatingDateWithKey&&(this._focusElement('[part="calendars"]:nth-of-type(2) .day--focused'),this._updatingDateWithKey=!1)}_focusElement(e){const t=this.shadowRoot.querySelector(e);t&&t.focus()}_renderHeaderSelectorButton(){const{yearFormat:e,dateFormat:t}=this._formatters,a="calendar"===this.startView,n=this._focusedDate,i=t(n),o=e(n);return r.qy`
    <button
      class="${(0,l.H)({"btn__year-selector":!0,selected:!a})}"
      type="button"
      part="year-selector"
      data-view="${"yearList"}"
      @click="${this._updateView("yearList")}">${o}</button>

    <div class="datepicker-toolbar" part="toolbar">
      <button
        class="${(0,l.H)({"btn__calendar-selector":!0,selected:a})}"
        type="button"
        part="calendar-selector"
        data-view="${"calendar"}"
        @click="${this._updateView("calendar")}">${i}</button>
    </div>
    `}_renderDatepickerYearList(){const{yearFormat:e}=this._formatters,t=this._focusedDate.getUTCFullYear();return r.qy`
    <div class="datepicker-body__year-list-view" part="year-list-view">
      <div class="year-list-view__full-list" part="year-list" @click="${this._updateYear}">
      ${this._yearList.map((a=>r.qy`<button
        class="${(0,l.H)({"year-list-view__list-item":!0,"year--selected":t===a})}"
        type="button"
        part="year"
        .year="${a}">${e((0,c.m)(a,0,1))}</button>`))}</div>
    </div>
    `}_renderDatepickerCalendar(){const{longMonthYearFormat:e,dayFormat:t,fullDateFormat:a,longWeekdayFormat:n,narrowWeekdayFormat:i}=this._formatters,o=(0,C.S)(this.disabledDays,Number),s=(0,C.S)(this.disabledDates,g.t),c=this.showWeekNumber,h=this._focusedDate,p=this.firstDayOfWeek,y=(0,g.t)(),m=this._selectedDate,_=this._max,b=this._min,{calendars:w,disabledDaysSet:k,disabledDatesSet:D,weekdays:x}=(0,v.n)({dayFormat:t,fullDateFormat:a,longWeekdayFormat:n,narrowWeekdayFormat:i,firstDayOfWeek:p,disabledDays:o,disabledDates:s,locale:this.locale,selectedDate:m,showWeekNumber:this.showWeekNumber,weekNumberType:this.weekNumberType,max:_,min:b,weekLabel:this.weekLabel}),T=!w[0].calendar.length,S=!w[2].calendar.length,F=x.map((e=>r.qy`<th
        class="calendar-weekday"
        part="calendar-weekday"
        role="columnheader"
        aria-label="${e.label}"
      >
        <div class="weekday" part="weekday">${e.value}</div>
      </th>`)),M=(0,d.u)(w,(e=>e.key),(({calendar:t},a)=>{if(!t.length)return r.qy`<div class="calendar-container" part="calendar"></div>`;const n=`calendarcaption${a}`,i=t[1][1].fullDate,o=1===a,s=o&&!this._isInVisibleMonth(h,m)?(0,f.Y)({disabledDaysSet:k,disabledDatesSet:D,hasAltKey:!1,keyCode:36,focusedDate:h,selectedDate:m,minTime:+b,maxTime:+_}):h;return r.qy`
      <div class="calendar-container" part="calendar">
        <table class="calendar-table" part="table" role="grid" aria-labelledby="${n}">
          <caption id="${n}">
            <div class="calendar-label" part="label">${i?e(i):""}</div>
          </caption>

          <thead role="rowgroup">
            <tr class="calendar-weekdays" part="weekdays" role="row">${F}</tr>
          </thead>

          <tbody role="rowgroup">${t.map((e=>r.qy`<tr role="row">${e.map(((e,t)=>{const{disabled:a,fullDate:n,label:i,value:d}=e;if(!n&&d&&c&&t<1)return r.qy`<th
                      class="full-calendar__day weekday-label"
                      part="calendar-day"
                      scope="row"
                      role="rowheader"
                      abbr="${i}"
                      aria-label="${i}"
                    >${d}</th>`;if(!d||!n)return r.qy`<td class="full-calendar__day day--empty" part="calendar-day"></td>`;const u=+new Date(n),p=+h===u,f=o&&s.getUTCDate()===Number(d);return r.qy`
                  <td
                    tabindex="${f?"0":"-1"}"
                    class="${(0,l.H)({"full-calendar__day":!0,"day--disabled":a,"day--today":+y===u,"day--focused":!a&&p})}"
                    part="calendar-day${+y===u?" calendar-today":""}"
                    role="gridcell"
                    aria-disabled="${a?"true":"false"}"
                    aria-label="${i}"
                    aria-selected="${p?"true":"false"}"
                    .fullDate="${n}"
                    .day="${d}"
                  >
                    <div
                      class="calendar-day"
                      part="day${+y===u?" today":""}"
                    >${d}</div>
                  </td>
                  `}))}</tr>`))}</tbody>
        </table>
      </div>
      `}));return this._disabledDatesSet=D,this._disabledDaysSet=k,r.qy`
    <div class="datepicker-body__calendar-view" part="calendar-view">
      <div class="calendar-view__month-selector" part="month-selectors">
        <div class="month-selector-container">${T?null:r.qy`
          <button
            class="btn__month-selector"
            type="button"
            part="month-selector"
            aria-label="Previous month"
            @click="${this._updateMonth("previous")}"
          >${u.K}</button>
        `}</div>

        <div class="month-selector-container">${S?null:r.qy`
          <button
            class="btn__month-selector"
            type="button"
            part="month-selector"
            aria-label="Next month"
            @click="${this._updateMonth("next")}"
          >${u.t}</button>
        `}</div>
      </div>

      <div
        class="${(0,l.H)({"calendars-container":!0,"has-min-date":T,"has-max-date":S})}"
        part="calendars"
        @keyup="${this._updateFocusedDateWithKeyboard}"
      >${M}</div>
    </div>
    `}_updateView(e){return(0,S.c)((()=>{"calendar"===e&&(this._selectedDate=this._lastSelectedDate=new Date((0,U.V)(this._focusedDate,this._min,this._max))),this._startView=e}))}_updateMonth(e){return(0,S.c)((()=>{if(null==this.calendarsContainer)return this.updateComplete;const t=this._lastSelectedDate||this._selectedDate,a=this._min,n=this._max,i="previous"===e,r=(0,c.m)(t.getUTCFullYear(),t.getUTCMonth()+(i?-1:1),1),o=r.getUTCFullYear(),s=r.getUTCMonth(),l=a.getUTCFullYear(),d=a.getUTCMonth(),u=n.getUTCFullYear(),h=n.getUTCMonth();return o<l||o<=l&&s<d||(o>u||o>=u&&s>h)||(this._lastSelectedDate=r,this._selectedDate=this._lastSelectedDate),this.updateComplete}))}_updateYear(e){const t=(0,_.z)(e,(e=>(0,D.n)(e,"year-list-view__list-item")));if(null==t)return;const a=(0,U.V)(new Date(this._focusedDate).setUTCFullYear(+t.year),this._min,this._max);this._selectedDate=this._lastSelectedDate=new Date(a),this._focusedDate=new Date(a),this._startView="calendar"}_updateFocusedDate(e){const t=(0,_.z)(e,(e=>(0,D.n)(e,"full-calendar__day")));null==t||["day--empty","day--disabled","day--focused","weekday-label"].some((e=>(0,D.n)(t,e)))||(this._focusedDate=new Date(t.fullDate),(0,m.w)(this,"datepicker-value-updated",{isKeypress:!1,value:this.value}))}_updateFocusedDateWithKeyboard(e){const t=e.keyCode;if(13===t||32===t)return(0,m.w)(this,"datepicker-value-updated",{keyCode:t,isKeypress:!0,value:this.value}),void(this._focusedDate=new Date(this._selectedDate));if(9===t||!p.YB.has(t))return;const a=this._selectedDate,n=(0,f.Y)({keyCode:t,selectedDate:a,disabledDatesSet:this._disabledDatesSet,disabledDaysSet:this._disabledDaysSet,focusedDate:this._focusedDate,hasAltKey:e.altKey,maxTime:+this._max,minTime:+this._min});this._isInVisibleMonth(n,a)||(this._selectedDate=this._lastSelectedDate=n),this._focusedDate=n,this._updatingDateWithKey=!0,(0,m.w)(this,"datepicker-value-updated",{keyCode:t,isKeypress:!0,value:this.value})}_isInVisibleMonth(e,t){const a=e.getUTCFullYear(),n=e.getUTCMonth(),i=t.getUTCFullYear(),r=t.getUTCMonth();return a===i&&n===r}get calendarsContainer(){return this.shadowRoot.querySelector(".calendars-container")}constructor(){super(),this.firstDayOfWeek=0,this.showWeekNumber=!1,this.weekNumberType="first-4-day-week",this.landscape=!1,this.locale=(0,k.f)(),this.disabledDays="",this.disabledDates="",this.weekLabel="Wk",this.inline=!1,this.dragRatio=.15,this._hasMin=!1,this._hasMax=!1,this._disabledDaysSet=new Set,this._disabledDatesSet=new Set,this._dx=-1/0,this._hasNativeWebAnimation="animate"in HTMLElement.prototype,this._updatingDateWithKey=!1;const e=(0,g.t)(),t=(0,w.G)(this.locale),a=(0,M.h)(e),n=(0,g.t)("2100-12-31");this.value=a,this.startView="calendar",this._min=new Date(e),this._max=new Date(n),this._todayDate=e,this._maxDate=n,this._yearList=(0,$.N)(e,n),this._selectedDate=new Date(e),this._focusedDate=new Date(e),this._formatters=t}}L.styles=[h.mm,h.WA,r.AH`
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
    `],(0,i.__decorate)([(0,o.MZ)({type:Number,reflect:!0})],L.prototype,"firstDayOfWeek",void 0),(0,i.__decorate)([(0,o.MZ)({type:Boolean,reflect:!0})],L.prototype,"showWeekNumber",void 0),(0,i.__decorate)([(0,o.MZ)({type:String,reflect:!0})],L.prototype,"weekNumberType",void 0),(0,i.__decorate)([(0,o.MZ)({type:Boolean,reflect:!0})],L.prototype,"landscape",void 0),(0,i.__decorate)([(0,o.MZ)({type:String,reflect:!0})],L.prototype,"startView",null),(0,i.__decorate)([(0,o.MZ)({type:String,reflect:!0})],L.prototype,"min",null),(0,i.__decorate)([(0,o.MZ)({type:String,reflect:!0})],L.prototype,"max",null),(0,i.__decorate)([(0,o.MZ)({type:String})],L.prototype,"value",null),(0,i.__decorate)([(0,o.MZ)({type:String})],L.prototype,"locale",void 0),(0,i.__decorate)([(0,o.MZ)({type:String})],L.prototype,"disabledDays",void 0),(0,i.__decorate)([(0,o.MZ)({type:String})],L.prototype,"disabledDates",void 0),(0,i.__decorate)([(0,o.MZ)({type:String})],L.prototype,"weekLabel",void 0),(0,i.__decorate)([(0,o.MZ)({type:Boolean})],L.prototype,"inline",void 0),(0,i.__decorate)([(0,o.MZ)({type:Number})],L.prototype,"dragRatio",void 0),(0,i.__decorate)([(0,o.MZ)({type:Date,attribute:!1})],L.prototype,"_selectedDate",void 0),(0,i.__decorate)([(0,o.MZ)({type:Date,attribute:!1})],L.prototype,"_focusedDate",void 0),(0,i.__decorate)([(0,o.MZ)({type:String,attribute:!1})],L.prototype,"_startView",void 0),(0,i.__decorate)([(0,o.P)(".year-list-view__full-list")],L.prototype,"_yearViewFullList",void 0),(0,i.__decorate)([(0,o.P)(".btn__year-selector")],L.prototype,"_buttonSelectorYear",void 0),(0,i.__decorate)([(0,o.P)(".year-list-view__list-item")],L.prototype,"_yearViewListItem",void 0),(0,i.__decorate)([(0,o.Ls)({passive:!0})],L.prototype,"_updateYear",null),(0,i.__decorate)([(0,o.Ls)({passive:!0})],L.prototype,"_updateFocusedDateWithKeyboard",null),n()}catch(L){n(L)}}))},58981:function(e,t,a){async function n(e,t){const{hasNativeWebAnimation:a=!1,keyframes:n=[],options:i={duration:100}}=t||{};if(Array.isArray(n)&&n.length)return new Promise((t=>{if(a){e.animate(n,i).onfinish=()=>t()}else{const[,a]=n||[],r=()=>{e.removeEventListener("transitionend",r),t()};e.addEventListener("transitionend",r),e.style.transitionDuration=`${i.duration}ms`,i.easing&&(e.style.transitionTimingFunction=i.easing),Object.keys(a).forEach((t=>{t&&(e.style[t]=a[t])}))}}))}a.d(t,{K:()=>n})},35676:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{Y:()=>d});var i=a(13192),r=a(52588),o=a(61881),s=e([r,o]);function d({hasAltKey:e,keyCode:t,focusedDate:a,selectedDate:n,disabledDaysSet:s,disabledDatesSet:l,minTime:d,maxTime:c}){const u=a.getUTCFullYear(),h=a.getUTCMonth(),p=a.getUTCDate(),y=+a,f=n.getUTCFullYear(),m=n.getUTCMonth();let _=u,b=h,w=p,v=!0;switch((m!==h||f!==u)&&(_=f,b=m,w=1,v=34===t||33===t||35===t),v){case y===d&&r.Gf.has(t):case y===c&&r.eB.has(t):break;case 38===t:w-=7;break;case 40===t:w+=7;break;case 37===t:w-=1;break;case 39===t:w+=1;break;case 34===t:e?_+=1:b+=1;break;case 33===t:e?_-=1:b-=1;break;case 35===t:b+=1,w=0;break;default:w=1}if(34===t||33===t){const e=(0,i.m)(_,b+1,0).getUTCDate();w>e&&(w=e)}return(0,o.i)({keyCode:t,maxTime:c,minTime:d,disabledDaysSet:s,disabledDatesSet:l,focusedDate:(0,i.m)(_,b,w)})}[r,o]=s.then?(await s)():s,n()}catch(l){n(l)}}))},12402:function(e,t,a){function n(e,t){window.customElements&&!window.customElements.get(e)&&window.customElements.define(e,t)}a.d(t,{U:()=>n})},82004:function(e,t,a){function n(e,t,a){return e.dispatchEvent(new CustomEvent(t,{detail:a,bubbles:!0,composed:!0}))}a.d(t,{w:()=>n})},24571:function(e,t,a){function n(e,t){return e.composedPath().find((e=>e instanceof HTMLElement&&t(e)))}a.d(t,{z:()=>n})},97076:function(e,t,a){function n(e,t){return+t-+e}a.d(t,{u:()=>n})},20335:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{G:()=>l});var i=a(36886),r=a(52588),o=e([r]);function l(e){const t=(0,r.B0)(e,{timeZone:"UTC",weekday:"short",month:"short",day:"numeric"}),a=(0,r.B0)(e,{timeZone:"UTC",day:"numeric"}),n=(0,r.B0)(e,{timeZone:"UTC",year:"numeric",month:"short",day:"numeric"}),o=(0,r.B0)(e,{timeZone:"UTC",year:"numeric",month:"long"}),s=(0,r.B0)(e,{timeZone:"UTC",weekday:"long"}),l=(0,r.B0)(e,{timeZone:"UTC",weekday:"narrow"}),d=(0,r.B0)(e,{timeZone:"UTC",year:"numeric"});return{locale:e,dateFormat:(0,i.f)(t),dayFormat:(0,i.f)(a),fullDateFormat:(0,i.f)(n),longMonthYearFormat:(0,i.f)(o),longWeekdayFormat:(0,i.f)(s),narrowWeekdayFormat:(0,i.f)(l),yearFormat:(0,i.f)(d)}}r=(o.then?(await o)():o)[0],n()}catch(s){n(s)}}))},86530:function(e,t,a){a.d(t,{n:()=>s});var n=a(13192);function i(e,t){const a=function(e,t){const a=t.getUTCFullYear(),i=t.getUTCMonth(),r=t.getUTCDate(),o=t.getUTCDay();let s=o;return"first-4-day-week"===e&&(s=3),"first-day-of-year"===e&&(s=6),"first-full-week"===e&&(s=0),(0,n.m)(a,i,r-o+s)}(e,t),i=(0,n.m)(a.getUTCFullYear(),0,1),r=1+(+a-+i)/864e5;return Math.ceil(r/7)}function r(e){if(e>=0&&e<7)return Math.abs(e);return((e<0?7*Math.ceil(Math.abs(e)):0)+e)%7}function o(e,t,a){const n=r(e-t);return a?1+n:n}function s(e){const{dayFormat:t,fullDateFormat:a,locale:s,longWeekdayFormat:l,narrowWeekdayFormat:d,selectedDate:c,disabledDates:u,disabledDays:h,firstDayOfWeek:p,max:y,min:f,showWeekNumber:m,weekLabel:_,weekNumberType:b}=e,w=null==f?Number.MIN_SAFE_INTEGER:+f,v=null==y?Number.MAX_SAFE_INTEGER:+y,g=function(e){const{firstDayOfWeek:t=0,showWeekNumber:a=!1,weekLabel:i,longWeekdayFormat:r,narrowWeekdayFormat:o}=e||{},s=1+(t+(t<0?7:0))%7,l=i||"Wk",d=a?[{label:"Wk"===l?"Week":l,value:l}]:[];return Array.from(Array(7)).reduce(((e,t,a)=>{const i=(0,n.m)(2017,0,s+a);return e.push({label:r(i),value:o(i)}),e}),d)}({longWeekdayFormat:l,narrowWeekdayFormat:d,firstDayOfWeek:p,showWeekNumber:m,weekLabel:_}),k=e=>[s,e.toJSON(),null==u?void 0:u.join("_"),null==h?void 0:h.join("_"),p,null==y?void 0:y.toJSON(),null==f?void 0:f.toJSON(),m,_,b].filter(Boolean).join(":"),D=c.getUTCFullYear(),x=c.getUTCMonth(),T=[-1,0,1].map((e=>{const l=(0,n.m)(D,x+e,1),d=+(0,n.m)(D,x+e+1,0),c=k(l);if(d<w||+l>v)return{key:c,calendar:[],disabledDatesSet:new Set,disabledDaysSet:new Set};const g=function(e){const{date:t,dayFormat:a,disabledDates:s=[],disabledDays:l=[],firstDayOfWeek:d=0,fullDateFormat:c,locale:u="en-US",max:h,min:p,showWeekNumber:y=!1,weekLabel:f="Week",weekNumberType:m="first-4-day-week"}=e||{},_=r(d),b=t.getUTCFullYear(),w=t.getUTCMonth(),v=(0,n.m)(b,w,1),g=new Set(l.map((e=>o(e,_,y)))),k=new Set(s.map((e=>+e))),D=[v.toJSON(),_,u,null==h?"":h.toJSON(),null==p?"":p.toJSON(),Array.from(g).join(","),Array.from(k).join(","),m].filter(Boolean).join(":"),x=o(v.getUTCDay(),_,y),T=null==p?+new Date("2000-01-01"):+p,S=null==h?+new Date("2100-12-31"):+h,C=y?8:7,F=(0,n.m)(b,1+w,0).getUTCDate(),M=[];let $=[],U=!1,N=1;for(const r of[0,1,2,3,4,5]){for(const e of[0,1,2,3,4,5,6].concat(7===C?[]:[7])){const t=e+r*C;if(!U&&y&&0===e){const e=r<1?_:0,t=i(m,(0,n.m)(b,w,N-e)),a=`${f} ${t}`;$.push({fullDate:null,label:a,value:`${t}`,key:`${D}:${a}`,disabled:!0});continue}if(U||t<x){$.push({fullDate:null,label:"",value:"",key:`${D}:${t}`,disabled:!0});continue}const o=(0,n.m)(b,w,N),s=+o,l=g.has(e)||k.has(s)||s<T||s>S;l&&k.add(s),$.push({fullDate:o,label:c(o),value:a(o),key:`${D}:${o.toJSON()}`,disabled:l}),N+=1,N>F&&(U=!0)}M.push($),$=[]}return{disabledDatesSet:k,calendar:M,disabledDaysSet:new Set(l.map((e=>r(e)))),key:D}}({dayFormat:t,fullDateFormat:a,locale:s,disabledDates:u,disabledDays:h,firstDayOfWeek:p,max:y,min:f,showWeekNumber:m,weekLabel:_,weekNumberType:b,date:l});return{...g,key:c}})),S=[],C=new Set,F=new Set;for(const n of T){const{disabledDatesSet:e,disabledDaysSet:t,...a}=n;if(a.calendar.length>0){if(t.size>0)for(const e of t)F.add(e);if(e.size>0)for(const t of e)C.add(t)}S.push(a)}return{calendars:S,weekdays:g,disabledDatesSet:C,disabledDaysSet:F,key:k(c)}}},57445:function(e,t,a){a.d(t,{t:()=>i});var n=a(13192);function i(e){const t=null==e?new Date:new Date(e),a="string"==typeof e&&(/^\d{4}-\d{2}-\d{2}$/i.test(e)||/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}(Z|\+00:00|-00:00)$/i.test(e)),i="number"==typeof e&&e>0&&isFinite(e);let r=t.getFullYear(),o=t.getMonth(),s=t.getDate();return(a||i)&&(r=t.getUTCFullYear(),o=t.getUTCMonth(),s=t.getUTCDate()),(0,n.m)(r,o,s)}},46719:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{f:()=>s});var i=a(52588),r=e([i]);function s(){return i.B0&&(0,i.B0)().resolvedOptions&&(0,i.B0)().resolvedOptions().locale||"en-US"}i=(r.then?(await r)():r)[0],n()}catch(o){n(o)}}))},61881:function(e,t,a){a.a(e,(async function(e,n){try{a.d(t,{i:()=>d});var i=a(13192),r=a(52588),o=a(97076),s=e([r]);function d({keyCode:e,disabledDaysSet:t,disabledDatesSet:a,focusedDate:n,maxTime:s,minTime:l}){const d=+n;let c=d<l,u=d>s;if((0,o.u)(l,s)<864e5)return n;let h=c||u||t.has(n.getUTCDay())||a.has(d);if(!h)return n;let p=0,y=c===u?n:new Date(c?l-864e5:864e5+s);const f=y.getUTCFullYear(),m=y.getUTCMonth();let _=y.getUTCDate();for(;h;)(c||!u&&r.$g.has(e))&&(_+=1),(u||!c&&r.tn.has(e))&&(_-=1),y=(0,i.m)(f,m,_),p=+y,c||(c=p<l,c&&(y=new Date(l),p=+y,_=y.getUTCDate())),u||(u=p>s,u&&(y=new Date(s),p=+y,_=y.getUTCDate())),h=t.has(y.getUTCDay())||a.has(p);return y}r=(s.then?(await s)():s)[0],n()}catch(l){n(l)}}))},47614:function(e,t,a){function n(e,t){return e.classList.contains(t)}a.d(t,{n:()=>n})},60117:function(e,t,a){function n(e,t){return!(null==e||!(t instanceof Date)||isNaN(+t))}a.d(t,{v:()=>n})},57407:function(e,t,a){function n(e){return e-Math.floor(e)>0?+e.toFixed(3):e}a.d(t,{b:()=>n})},447:function(e,t,a){function n(e){return{passive:!0,handleEvent:e}}a.d(t,{c:()=>n})},84073:function(e,t,a){function n(e,t){const a="string"==typeof e&&e.length>0?e.split(/,\s*/i):[];return a.length?"function"==typeof t?a.map(t):a:[]}a.d(t,{S:()=>n})},30622:function(e,t,a){function n(e,t){if(null==e.scrollTo){const{top:a,left:n}=t||{};e.scrollTop=a||0,e.scrollLeft=n||0}else e.scrollTo(t)}a.d(t,{G:()=>n})},49060:function(e,t,a){function n(e){if(e instanceof Date&&!isNaN(+e)){const t=e.toJSON();return null==t?"":t.replace(/^(.+)T.+/i,"$1")}return""}a.d(t,{h:()=>n})},93739:function(e,t,a){a.d(t,{N:()=>i});var n=a(97076);function i(e,t){if((0,n.u)(e,t)<864e5)return[];const a=e.getUTCFullYear();return Array.from(Array(t.getUTCFullYear()-a+1),((e,t)=>t+a))}},74745:function(e,t,a){function n(e,t,a){const n="number"==typeof e?e:+e,i=+t,r=+a;return n<i?i:n>r?r:e}a.d(t,{V:()=>n})},46977:function(e,t,a){a.d(t,{J:()=>s});var n=a(12130);function i(e){const{clientX:t,clientY:a,pageX:n,pageY:i}=e,r=Math.max(n,t),o=Math.max(i,a),s=e.identifier||e.pointerId;return{x:r,y:o,id:null==s?0:s}}function r(e,t){const a=t.changedTouches;if(null==a)return{newPointer:i(t),oldPointer:e};const n=Array.from(a,(e=>i(e)));return{newPointer:null==e?n[0]:n.find((t=>t.id===e.id)),oldPointer:e}}function o(e,t,a){e.addEventListener(t,a,!!n.QQ&&{passive:!0})}class s{disconnect(){const e=this._element;e&&e.removeEventListener&&(e.removeEventListener("mousedown",this._down),e.removeEventListener("touchstart",this._down),e.removeEventListener("touchmove",this._move),e.removeEventListener("touchend",this._up))}_onDown(e){return t=>{t instanceof MouseEvent&&(this._element.addEventListener("mousemove",this._move),this._element.addEventListener("mouseup",this._up),this._element.addEventListener("mouseleave",this._up));const{newPointer:a}=r(this._startPointer,t);e(a,t),this._startPointer=a}}_onMove(e){return t=>{this._updatePointers(e,t)}}_onUp(e){return t=>{this._updatePointers(e,t,!0)}}_updatePointers(e,t,a){a&&t instanceof MouseEvent&&(this._element.removeEventListener("mousemove",this._move),this._element.removeEventListener("mouseup",this._up),this._element.removeEventListener("mouseleave",this._up));const{newPointer:n,oldPointer:i}=r(this._startPointer,t);e(n,i,t),this._startPointer=a?null:n}constructor(e,t){this._element=e,this._startPointer=null;const{down:a,move:n,up:i}=t;this._down=this._onDown(a),this._move=this._onMove(n),this._up=this._onUp(i),e&&e.addEventListener&&(e.addEventListener("mousedown",this._down),o(e,"touchstart",this._down),o(e,"touchmove",this._move),o(e,"touchend",this._up))}}},2045:function(e,t,a){a.d(t,{q:()=>i});let n={};function i(){return n}},74816:function(e,t,a){a.d(t,{x:()=>i});var n=a(73420);function i(e,...t){const a=n.w.bind(null,e||t.find((e=>"object"==typeof e)));return t.map(a)}},9160:function(e,t,a){a.d(t,{Cg:()=>r,_P:()=>s,my:()=>n,s0:()=>o,w4:()=>i});Math.pow(10,8);const n=6048e5,i=864e5,r=6e4,o=36e5,s=Symbol.for("constructDateFrom")},73420:function(e,t,a){a.d(t,{w:()=>i});var n=a(9160);function i(e,t){return"function"==typeof e?e(t):e&&"object"==typeof e&&n._P in e?e[n._P](t):e instanceof Date?new e.constructor(t):new Date(t)}},3952:function(e,t,a){a.d(t,{m:()=>l});var n=a(83504);function i(e){const t=(0,n.a)(e),a=new Date(Date.UTC(t.getFullYear(),t.getMonth(),t.getDate(),t.getHours(),t.getMinutes(),t.getSeconds(),t.getMilliseconds()));return a.setUTCFullYear(t.getFullYear()),+e-+a}var r=a(74816),o=a(9160),s=a(35932);function l(e,t,a){const[n,l]=(0,r.x)(a?.in,e,t),d=(0,s.o)(n),c=(0,s.o)(l),u=+d-i(d),h=+c-i(c);return Math.round((u-h)/o.w4)}},35932:function(e,t,a){a.d(t,{o:()=>i});var n=a(83504);function i(e,t){const a=(0,n.a)(e,t?.in);return a.setHours(0,0,0,0),a}},52640:function(e,t,a){a.d(t,{k:()=>r});var n=a(2045),i=a(83504);function r(e,t){const a=(0,n.q)(),r=t?.weekStartsOn??t?.locale?.options?.weekStartsOn??a.weekStartsOn??a.locale?.options?.weekStartsOn??0,o=(0,i.a)(e,t?.in),s=o.getDay(),l=(s<r?7:0)+s-r;return o.setDate(o.getDate()-l),o.setHours(0,0,0,0),o}},83504:function(e,t,a){a.d(t,{a:()=>i});var n=a(73420);function i(e,t){return(0,n.w)(t||e,e)}},57378:function(e,t,a){a.d(t,{P:()=>s});var n=a(5055),i=a(42017),r=a(63937);const o=e=>(0,r.ps)(e)?e._$litType$.h:e.strings,s=(0,i.u$)(class extends i.WL{render(e){return[e]}update(e,[t]){const a=(0,r.qb)(this.it)?o(this.it):null,i=(0,r.qb)(t)?o(t):null;if(null!==a&&(null===i||a!==i)){const t=(0,r.cN)(e).pop();let i=this.et.get(a);if(void 0===i){const e=document.createDocumentFragment();i=(0,n.XX)(n.s6,e),i.setConnected(!1),this.et.set(a,i)}(0,r.mY)(i,[t]),(0,r.Dx)(i,void 0,t)}if(null!==i){if(null===a||a!==i){const t=this.et.get(i);if(void 0!==t){const a=(0,r.cN)(t).pop();(0,r.Jz)(e),(0,r.Dx)(e,void 0,a),(0,r.mY)(e,[a])}}this.it=t}else this.it=void 0;return this.render(t)}constructor(e){super(e),this.et=new WeakMap}})},36886:function(e,t,a){function n(e){return t=>e.format(t).replace(/\u200e/gi,"")}a.d(t,{f:()=>n})},13192:function(e,t,a){function n(e,t,a){return new Date(Date.UTC(e,t,a))}a.d(t,{m:()=>n})}};
//# sourceMappingURL=706.ab2f8ffb3c13502e.js.map