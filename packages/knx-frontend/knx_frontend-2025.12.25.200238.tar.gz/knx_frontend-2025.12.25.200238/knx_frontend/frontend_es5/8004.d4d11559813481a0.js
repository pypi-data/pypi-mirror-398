"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8004"],{42256:function(e,t,i){i.d(t,{I:function(){return r}});var s=i(44734),a=i(56038),n=(i(16280),i(25276),i(44114),i(54554),i(18111),i(7588),i(33110),i(26099),i(58335),i(23500),function(){return(0,a.A)((function e(){var t=arguments.length>0&&void 0!==arguments[0]?arguments[0]:window.localStorage;(0,s.A)(this,e),this._storage={},this._listeners={},this.storage=t,this.storage===window.localStorage&&window.addEventListener("storage",(e=>{e.key&&this.hasKey(e.key)&&(this._storage[e.key]=e.newValue?JSON.parse(e.newValue):e.newValue,this._listeners[e.key]&&this._listeners[e.key].forEach((t=>t(e.oldValue?JSON.parse(e.oldValue):e.oldValue,this._storage[e.key]))))}))}),[{key:"addFromStorage",value:function(e){if(!this._storage[e]){var t=this.storage.getItem(e);t&&(this._storage[e]=JSON.parse(t))}}},{key:"subscribeChanges",value:function(e,t){return this._listeners[e]?this._listeners[e].push(t):this._listeners[e]=[t],()=>{this.unsubscribeChanges(e,t)}}},{key:"unsubscribeChanges",value:function(e,t){if(e in this._listeners){var i=this._listeners[e].indexOf(t);-1!==i&&this._listeners[e].splice(i,1)}}},{key:"hasKey",value:function(e){return e in this._storage}},{key:"getValue",value:function(e){return this._storage[e]}},{key:"setValue",value:function(e,t){var i=this._storage[e];this._storage[e]=t;try{void 0===t?this.storage.removeItem(e):this.storage.setItem(e,JSON.stringify(t))}catch(s){}finally{this._listeners[e]&&this._listeners[e].forEach((e=>e(i,t)))}}}])}()),o={};function r(e){return(t,i)=>{if("object"==typeof i)throw new Error("This decorator does not support this compilation type.");var s,a=e.storage||"localStorage";a&&a in o?s=o[a]:(s=new n(window[a]),o[a]=s);var r=e.key||String(i);s.addFromStorage(r);var l=!1!==e.subscribe?e=>s.subscribeChanges(r,((t,s)=>{e.requestUpdate(i,t)})):void 0,d=()=>s.hasKey(r)?e.deserializer?e.deserializer(s.getValue(r)):s.getValue(r):void 0,c=(t,a)=>{var n;e.state&&(n=d()),s.setValue(r,e.serializer?e.serializer(a):a),e.state&&t.requestUpdate(i,n)},h=t.performUpdate;if(t.performUpdate=function(){this.__initialized=!0,h.call(this)},e.subscribe){var u=t.connectedCallback,p=t.disconnectedCallback;t.connectedCallback=function(){u.call(this);this.__unbsubLocalStorage||(this.__unbsubLocalStorage=null==l?void 0:l(this))},t.disconnectedCallback=function(){var e;p.call(this);var t=this;null===(e=t.__unbsubLocalStorage)||void 0===e||e.call(t),t.__unbsubLocalStorage=void 0}}var _,v=Object.getOwnPropertyDescriptor(t,i);if(void 0===v)_={get(){return d()},set(e){(this.__initialized||void 0===d())&&c(this,e)},configurable:!0,enumerable:!0};else{var g=v.set;_=Object.assign(Object.assign({},v),{},{get(){return d()},set(e){(this.__initialized||void 0===d())&&c(this,e),null==g||g.call(this,e)}})}Object.defineProperty(t,i,_)}}},48206:function(e,t,i){var s,a,n,o,r,l,d,c,h,u,p=i(31432),_=i(94741),v=i(61397),g=i(50264),m=i(44734),f=i(56038),y=i(69683),b=i(6454),k=i(25460),x=(i(28706),i(23792),i(62062),i(44114),i(54743),i(11745),i(16573),i(78100),i(77936),i(18111),i(61701),i(26099),i(42762),i(72107),i(21489),i(48140),i(75044),i(21903),i(91134),i(28845),i(373),i(41405),i(37467),i(44732),i(33684),i(79577),i(41549),i(49797),i(49631),i(35623),i(62826)),A=i(96196),w=i(77845),M=i(94333),L=i(9477),$=i(45369),C=i(98320),I=i(10234),S=(i(62953),i(3296),i(27208),i(48408),i(14603),i(47566),i(98721),function(){return(0,f.A)((function e(t){(0,m.A)(this,e),this._active=!1,this._callback=t}),[{key:"active",get:function(){return this._active}},{key:"sampleRate",get:function(){var e;return null===(e=this._context)||void 0===e?void 0:e.sampleRate}},{key:"start",value:(s=(0,g.A)((0,v.A)().m((function e(){var t;return(0,v.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(this._context&&this._stream&&this._source&&this._recorder){e.n=5;break}return e.p=1,e.n=2,this._createContext();case 2:e.n=4;break;case 3:e.p=3,t=e.v,console.error(t),this._active=!1;case 4:e.n=7;break;case 5:return this._stream.getTracks()[0].enabled=!0,e.n=6,this._context.resume();case 6:this._active=!0;case 7:return e.a(2)}}),e,this,[[1,3]])}))),function(){return s.apply(this,arguments)})},{key:"stop",value:(t=(0,g.A)((0,v.A)().m((function e(){var t;return(0,v.A)().w((function(e){for(;;)switch(e.n){case 0:return this._active=!1,this._stream&&(this._stream.getTracks()[0].enabled=!1),e.n=1,null===(t=this._context)||void 0===t?void 0:t.suspend();case 1:return e.a(2)}}),e,this)}))),function(){return t.apply(this,arguments)})},{key:"close",value:function(){var e,t,i;this._active=!1,null===(e=this._stream)||void 0===e||e.getTracks()[0].stop(),this._recorder&&(this._recorder.port.onmessage=null),null===(t=this._source)||void 0===t||t.disconnect(),null===(i=this._context)||void 0===i||i.close(),this._stream=void 0,this._source=void 0,this._recorder=void 0,this._context=void 0}},{key:"_createContext",value:(e=(0,g.A)((0,v.A)().m((function e(){var t;return(0,v.A)().w((function(e){for(;;)switch(e.n){case 0:return t=new(AudioContext||webkitAudioContext),e.n=1,navigator.mediaDevices.getUserMedia({audio:!0});case 1:return this._stream=e.v,e.n=2,t.audioWorklet.addModule(new URL(i(12889),i.b));case 2:this._context=t,this._source=this._context.createMediaStreamSource(this._stream),this._recorder=new AudioWorkletNode(this._context,"recorder-worklet"),this._recorder.port.onmessage=e=>{this._active&&this._callback(e.data)},this._active=!0,this._source.connect(this._recorder);case 3:return e.a(2)}}),e,this)}))),function(){return e.apply(this,arguments)})}],[{key:"isSupported",get:function(){return window.isSecureContext&&(window.AudioContext||window.webkitAudioContext)}}]);var e,t,s}()),B=i(62001),z=(i(17963),i(28089),i(78740),e=>e),q=function(e){function t(){var e;(0,m.A)(this,t);for(var i=arguments.length,s=new Array(i),a=0;a<i;a++)s[a]=arguments[a];return(e=(0,y.A)(this,t,[].concat(s))).disableSpeech=!1,e._conversation=[],e._showSendButton=!1,e._processing=!1,e._conversationId=null,e._unloadAudio=()=>{e._audio&&(e._audio.pause(),e._audio.removeAttribute("src"),e._audio=void 0)},e}return(0,b.A)(t,e),(0,f.A)(t,[{key:"willUpdate",value:function(e){this.hasUpdated&&!e.has("pipeline")||(this._conversation=[{who:"hass",text:this.hass.localize("ui.dialogs.voice_command.how_can_i_help")}])}},{key:"firstUpdated",value:function(e){(0,k.A)(t,"firstUpdated",this,3)([e]),this.startListening&&this.pipeline&&this.pipeline.stt_engine&&S.isSupported&&this._toggleListening(),setTimeout((()=>this._messageInput.focus()),0)}},{key:"updated",value:function(e){(0,k.A)(t,"updated",this,3)([e]),e.has("_conversation")&&this._scrollMessagesBottom()}},{key:"disconnectedCallback",value:function(){var e;(0,k.A)(t,"disconnectedCallback",this,3)([]),null===(e=this._audioRecorder)||void 0===e||e.close(),this._unloadAudio()}},{key:"render",value:function(){var e,t,i=!!this.pipeline&&(this.pipeline.prefer_local_intents||!this.hass.states[this.pipeline.conversation_engine]||(0,L.$)(this.hass.states[this.pipeline.conversation_engine],C.ZE.CONTROL)),c=S.isSupported,h=(null===(e=this.pipeline)||void 0===e?void 0:e.stt_engine)&&!this.disableSpeech;return(0,A.qy)(s||(s=z`
      <div class="messages">
        ${0}
        <div class="spacer"></div>
        ${0}
      </div>
      <div class="input" slot="primaryAction">
        <ha-textfield
          id="message-input"
          @keyup=${0}
          @input=${0}
          .label=${0}
          .iconTrailing=${0}
        >
          <div slot="trailingIcon">
            ${0}
          </div>
        </ha-textfield>
      </div>
    `),i?A.s6:(0,A.qy)(a||(a=z`
              <ha-alert>
                ${0}
              </ha-alert>
            `),this.hass.localize("ui.dialogs.voice_command.conversation_no_control")),this._conversation.map((e=>(0,A.qy)(n||(n=z`
            <ha-markdown
              class="message ${0}"
              breaks
              cache
              .content=${0}
            >
            </ha-markdown>
          `),(0,M.H)({error:!!e.error,[e.who]:!0}),e.text))),this._handleKeyUp,this._handleInput,this.hass.localize("ui.dialogs.voice_command.input_label"),!0,this._showSendButton||!h?(0,A.qy)(o||(o=z`
                  <ha-icon-button
                    class="listening-icon"
                    .path=${0}
                    @click=${0}
                    .disabled=${0}
                    .label=${0}
                  >
                  </ha-icon-button>
                `),"M2,21L23,12L2,3V10L17,12L2,14V21Z",this._handleSendMessage,this._processing,this.hass.localize("ui.dialogs.voice_command.send_text")):(0,A.qy)(r||(r=z`
                  ${0}

                  <div class="listening-icon">
                    <ha-icon-button
                      .path=${0}
                      @click=${0}
                      .disabled=${0}
                      .label=${0}
                    >
                    </ha-icon-button>
                    ${0}
                  </div>
                `),null!==(t=this._audioRecorder)&&void 0!==t&&t.active?(0,A.qy)(l||(l=z`
                        <div class="bouncer">
                          <div class="double-bounce1"></div>
                          <div class="double-bounce2"></div>
                        </div>
                      `)):A.s6,"M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z",this._handleListeningButton,this._processing,this.hass.localize("ui.dialogs.voice_command.start_listening"),c?null:(0,A.qy)(d||(d=z`
                          <ha-svg-icon
                            .path=${0}
                            class="unsupported"
                          ></ha-svg-icon>
                        `),"M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z")))}},{key:"_scrollMessagesBottom",value:(q=(0,g.A)((0,v.A)().m((function e(){var t,i;return(0,v.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if((t=this._lastChatMessage).hasUpdated){e.n=1;break}return e.n=1,t.updateComplete;case 1:if(!this._lastChatMessageImage||this._lastChatMessageImage.naturalHeight){e.n=5;break}return e.p=2,e.n=3,this._lastChatMessageImage.decode();case 3:e.n=5;break;case 4:e.p=4,i=e.v,console.warn("Failed to decode image:",i);case 5:t.getBoundingClientRect().y<this.getBoundingClientRect().top+24||t.scrollIntoView({behavior:"smooth",block:"start"});case 6:return e.a(2)}}),e,this,[[2,4]])}))),function(){return q.apply(this,arguments)})},{key:"_handleKeyUp",value:function(e){var t=e.target;!this._processing&&"Enter"===e.key&&t.value&&(this._processText(t.value),t.value="",this._showSendButton=!1)}},{key:"_handleInput",value:function(e){var t=e.target.value;t&&!this._showSendButton?this._showSendButton=!0:!t&&this._showSendButton&&(this._showSendButton=!1)}},{key:"_handleSendMessage",value:function(){this._messageInput.value&&(this._processText(this._messageInput.value.trim()),this._messageInput.value="",this._showSendButton=!1)}},{key:"_handleListeningButton",value:function(e){e.stopPropagation(),e.preventDefault(),this._toggleListening()}},{key:"_toggleListening",value:(w=(0,g.A)((0,v.A)().m((function e(){var t;return(0,v.A)().w((function(e){for(;;)switch(e.n){case 0:if(S.isSupported){e.n=1;break}return this._showNotSupportedMessage(),e.a(2);case 1:null!==(t=this._audioRecorder)&&void 0!==t&&t.active?this._stopListening():this._startListening();case 2:return e.a(2)}}),e,this)}))),function(){return w.apply(this,arguments)})},{key:"_addMessage",value:function(e){this._conversation=[].concat((0,_.A)(this._conversation),[e])}},{key:"_showNotSupportedMessage",value:(x=(0,g.A)((0,v.A)().m((function e(){return(0,v.A)().w((function(e){for(;;)switch(e.n){case 0:this._addMessage({who:"hass",text:(0,A.qy)(c||(c=z`${0}

        ${0}`),this.hass.localize("ui.dialogs.voice_command.not_supported_microphone_browser"),this.hass.localize("ui.dialogs.voice_command.not_supported_microphone_documentation",{documentation_link:(0,A.qy)(h||(h=z`<a
                target="_blank"
                rel="noopener noreferrer"
                href=${0}
              >${0}</a>`),(0,B.o)(this.hass,"/docs/configuration/securing/#remote-access"),this.hass.localize("ui.dialogs.voice_command.not_supported_microphone_documentation_link"))}))});case 1:return e.a(2)}}),e,this)}))),function(){return x.apply(this,arguments)})},{key:"_startListening",value:(u=(0,g.A)((0,v.A)().m((function e(){var t,i,s,a,n,o;return(0,v.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this._unloadAudio(),this._processing=!0,this._audioRecorder||(this._audioRecorder=new S((e=>{this._audioBuffer?this._audioBuffer.push(e):this._sendAudioChunk(e)}))),this._stt_binary_handler_id=void 0,this._audioBuffer=[],t={who:"user",text:"…"},e.n=1,this._audioRecorder.start();case 1:return this._addMessage(t),i=this._createAddHassMessageProcessor(),e.p=2,e.n=3,(0,$.vU)(this.hass,(e=>{if("run-start"===e.type)this._stt_binary_handler_id=e.data.runner_data.stt_binary_handler_id,this._audio=new Audio(e.data.tts_output.url),this._audio.play(),this._audio.addEventListener("ended",(()=>{this._unloadAudio(),i.continueConversation&&this._startListening()})),this._audio.addEventListener("pause",this._unloadAudio),this._audio.addEventListener("canplaythrough",(()=>{var e;return null===(e=this._audio)||void 0===e?void 0:e.play()})),this._audio.addEventListener("error",(()=>{this._unloadAudio(),(0,I.K$)(this,{title:"Error playing audio."})}));else if("stt-start"===e.type&&this._audioBuffer){var s,a=(0,p.A)(this._audioBuffer);try{for(a.s();!(s=a.n()).done;){var o=s.value;this._sendAudioChunk(o)}}catch(r){a.e(r)}finally{a.f()}this._audioBuffer=void 0}else"stt-end"===e.type?(this._stt_binary_handler_id=void 0,this._stopListening(),t.text=e.data.stt_output.text,this.requestUpdate("_conversation"),i.addMessage()):e.type.startsWith("intent-")?i.processEvent(e):"run-end"===e.type?(this._stt_binary_handler_id=void 0,n()):"error"===e.type&&(this._unloadAudio(),this._stt_binary_handler_id=void 0,"…"===t.text?(t.text=e.data.message,t.error=!0):i.setError(e.data.message),this._stopListening(),this.requestUpdate("_conversation"),n())}),{start_stage:"stt",end_stage:null!==(s=this.pipeline)&&void 0!==s&&s.tts_engine?"tts":"intent",input:{sample_rate:this._audioRecorder.sampleRate},pipeline:null===(a=this.pipeline)||void 0===a?void 0:a.id,conversation_id:this._conversationId});case 3:n=e.v,e.n=6;break;case 4:return e.p=4,o=e.v,e.n=5,(0,I.K$)(this,{title:"Error starting pipeline",text:o.message||o});case 5:this._stopListening();case 6:return e.p=6,this._processing=!1,e.f(6);case 7:return e.a(2)}}),e,this,[[2,4,6,7]])}))),function(){return u.apply(this,arguments)})},{key:"_stopListening",value:function(){var e;if(null===(e=this._audioRecorder)||void 0===e||e.stop(),this.requestUpdate("_audioRecorder"),this._stt_binary_handler_id){if(this._audioBuffer){var t,i=(0,p.A)(this._audioBuffer);try{for(i.s();!(t=i.n()).done;){var s=t.value;this._sendAudioChunk(s)}}catch(a){i.e(a)}finally{i.f()}}this._sendAudioChunk(new Int16Array),this._stt_binary_handler_id=void 0}this._audioBuffer=void 0}},{key:"_sendAudioChunk",value:function(e){if(this.hass.connection.socket.binaryType="arraybuffer",null!=this._stt_binary_handler_id){var t=new Uint8Array(1+2*e.length);t[0]=this._stt_binary_handler_id,t.set(new Uint8Array(e.buffer),1),this.hass.connection.socket.send(t)}}},{key:"_processText",value:(i=(0,g.A)((0,v.A)().m((function e(t){var i,s,a;return(0,v.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this._unloadAudio(),this._processing=!0,this._addMessage({who:"user",text:t}),(i=this._createAddHassMessageProcessor()).addMessage(),e.p=1,e.n=2,(0,$.vU)(this.hass,(e=>{e.type.startsWith("intent-")&&i.processEvent(e),"intent-end"===e.type&&a(),"error"===e.type&&(i.setError(e.data.message),a())}),{start_stage:"intent",input:{text:t},end_stage:"intent",pipeline:null===(s=this.pipeline)||void 0===s?void 0:s.id,conversation_id:this._conversationId});case 2:a=e.v,e.n=4;break;case 3:e.p=3,e.v,i.setError(this.hass.localize("ui.dialogs.voice_command.error"));case 4:return e.p=4,this._processing=!1,e.f(4);case 5:return e.a(2)}}),e,this,[[1,3,4,5]])}))),function(e){return i.apply(this,arguments)})},{key:"_createAddHassMessageProcessor",value:function(){var e="",t=()=>{"…"!==s.hassMessage.text&&(s.hassMessage.text=s.hassMessage.text.substring(0,s.hassMessage.text.length-1),s.hassMessage={who:"hass",text:"…",error:!1},this._addMessage(s.hassMessage))},i={},s={continueConversation:!1,hassMessage:{who:"hass",text:"…",error:!1},addMessage:()=>{this._addMessage(s.hassMessage)},setError:e=>{t(),s.hassMessage.text=e,s.hassMessage.error=!0,this.requestUpdate("_conversation")},processEvent:a=>{if("intent-progress"===a.type&&a.data.chat_log_delta){var n=a.data.chat_log_delta;if(n.role&&(t(),e=n.role),"assistant"===e){if(n.content&&(s.hassMessage.text=s.hassMessage.text.substring(0,s.hassMessage.text.length-1)+n.content+"…",this.requestUpdate("_conversation")),n.tool_calls){var o,r=(0,p.A)(n.tool_calls);try{for(r.s();!(o=r.n()).done;){var l=o.value;i[l.id]=l}}catch(h){r.e(h)}finally{r.f()}}}else"tool_result"===e&&i[n.tool_call_id]&&delete i[n.tool_call_id]}else if("intent-end"===a.type){var d;this._conversationId=a.data.intent_output.conversation_id,s.continueConversation=a.data.intent_output.continue_conversation;var c=null===(d=a.data.intent_output.response.speech)||void 0===d?void 0:d.plain.speech;if(!c)return;"error"===a.data.intent_output.response.response_type?s.setError(c):(s.hassMessage.text=c,this.requestUpdate("_conversation"))}}};return s}}]);var i,u,x,w,q}(A.WF);q.styles=(0,A.AH)(u||(u=z`
    :host {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    ha-alert {
      margin-bottom: 8px;
    }
    ha-textfield {
      display: block;
    }
    .messages {
      flex: 1;
      display: block;
      box-sizing: border-box;
      overflow-y: auto;
      max-height: 100%;
      display: flex;
      flex-direction: column;
      padding: 0 12px 16px;
    }
    .spacer {
      flex: 1;
    }
    .message {
      font-size: var(--ha-font-size-l);
      clear: both;
      max-width: -webkit-fill-available;
      overflow-wrap: break-word;
      scroll-margin-top: 24px;
      margin: 8px 0;
      padding: 8px;
      border-radius: var(--ha-border-radius-xl);
    }
    @media all and (max-width: 450px), all and (max-height: 500px) {
      .message {
        font-size: var(--ha-font-size-l);
      }
    }
    .message.user {
      margin-left: 24px;
      margin-inline-start: 24px;
      margin-inline-end: initial;
      align-self: flex-end;
      border-bottom-right-radius: 0px;
      --markdown-link-color: var(--text-primary-color);
      background-color: var(--chat-background-color-user, var(--primary-color));
      color: var(--text-primary-color);
      direction: var(--direction);
    }
    .message.hass {
      margin-right: 24px;
      margin-inline-end: 24px;
      margin-inline-start: initial;
      align-self: flex-start;
      border-bottom-left-radius: 0px;
      background-color: var(
        --chat-background-color-hass,
        var(--secondary-background-color)
      );

      color: var(--primary-text-color);
      direction: var(--direction);
    }
    .message.error {
      background-color: var(--error-color);
      color: var(--text-primary-color);
    }
    ha-markdown {
      --markdown-image-border-radius: calc(var(--ha-border-radius-xl) / 2);
      --markdown-table-border-color: var(--divider-color);
      --markdown-code-background-color: var(--primary-background-color);
      --markdown-code-text-color: var(--primary-text-color);
      --markdown-list-indent: 1rem;
      &:not(:has(ha-markdown-element)) {
        min-height: 1lh;
        min-width: 1lh;
        flex-shrink: 0;
      }
    }
    .bouncer {
      width: 48px;
      height: 48px;
      position: absolute;
    }
    .double-bounce1,
    .double-bounce2 {
      width: 48px;
      height: 48px;
      border-radius: var(--ha-border-radius-circle);
      background-color: var(--primary-color);
      opacity: 0.2;
      position: absolute;
      top: 0;
      left: 0;
      -webkit-animation: sk-bounce 2s infinite ease-in-out;
      animation: sk-bounce 2s infinite ease-in-out;
    }
    .double-bounce2 {
      -webkit-animation-delay: -1s;
      animation-delay: -1s;
    }
    @-webkit-keyframes sk-bounce {
      0%,
      100% {
        -webkit-transform: scale(0);
      }
      50% {
        -webkit-transform: scale(1);
      }
    }
    @keyframes sk-bounce {
      0%,
      100% {
        transform: scale(0);
        -webkit-transform: scale(0);
      }
      50% {
        transform: scale(1);
        -webkit-transform: scale(1);
      }
    }

    .listening-icon {
      position: relative;
      color: var(--secondary-text-color);
      margin-right: -24px;
      margin-inline-end: -24px;
      margin-inline-start: initial;
      direction: var(--direction);
      transform: scaleX(var(--scale-direction));
    }

    .listening-icon[active] {
      color: var(--primary-color);
    }

    .unsupported {
      color: var(--error-color);
      position: absolute;
      --mdc-icon-size: 16px;
      right: 5px;
      inset-inline-end: 5px;
      inset-inline-start: initial;
      top: 0px;
    }
  `)),(0,x.__decorate)([(0,w.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,x.__decorate)([(0,w.MZ)({attribute:!1})],q.prototype,"pipeline",void 0),(0,x.__decorate)([(0,w.MZ)({type:Boolean,attribute:"disable-speech"})],q.prototype,"disableSpeech",void 0),(0,x.__decorate)([(0,w.MZ)({type:Boolean,attribute:!1})],q.prototype,"startListening",void 0),(0,x.__decorate)([(0,w.P)("#message-input")],q.prototype,"_messageInput",void 0),(0,x.__decorate)([(0,w.P)(".message:last-child")],q.prototype,"_lastChatMessage",void 0),(0,x.__decorate)([(0,w.P)(".message:last-child img:last-of-type")],q.prototype,"_lastChatMessageImage",void 0),(0,x.__decorate)([(0,w.wk)()],q.prototype,"_conversation",void 0),(0,x.__decorate)([(0,w.wk)()],q.prototype,"_showSendButton",void 0),(0,x.__decorate)([(0,w.wk)()],q.prototype,"_processing",void 0),q=(0,x.__decorate)([(0,w.EM)("ha-assist-chat")],q)},16857:function(e,t,i){var s,a,n=i(44734),o=i(56038),r=i(69683),l=i(6454),d=i(25460),c=(i(28706),i(18111),i(7588),i(2892),i(26099),i(23500),i(62826)),h=i(96196),u=i(77845),p=i(76679),_=(i(41742),i(1554),e=>e),v=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,s=new Array(i),a=0;a<i;a++)s[a]=arguments[a];return(e=(0,r.A)(this,t,[].concat(s))).corner="BOTTOM_START",e.menuCorner="START",e.x=null,e.y=null,e.multi=!1,e.activatable=!1,e.disabled=!1,e.fixed=!1,e.noAnchor=!1,e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"items",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.items}},{key:"selected",get:function(){var e;return null===(e=this._menu)||void 0===e?void 0:e.selected}},{key:"focus",value:function(){var e,t;null!==(e=this._menu)&&void 0!==e&&e.open?this._menu.focusItemAtIndex(0):null===(t=this._triggerButton)||void 0===t||t.focus()}},{key:"render",value:function(){return(0,h.qy)(s||(s=_`
      <div @click=${0}>
        <slot name="trigger" @slotchange=${0}></slot>
      </div>
      <ha-menu
        .corner=${0}
        .menuCorner=${0}
        .fixed=${0}
        .multi=${0}
        .activatable=${0}
        .y=${0}
        .x=${0}
      >
        <slot></slot>
      </ha-menu>
    `),this._handleClick,this._setTriggerAria,this.corner,this.menuCorner,this.fixed,this.multi,this.activatable,this.y,this.x)}},{key:"firstUpdated",value:function(e){(0,d.A)(t,"firstUpdated",this,3)([e]),"rtl"===p.G.document.dir&&this.updateComplete.then((()=>{this.querySelectorAll("ha-list-item").forEach((e=>{var t=document.createElement("style");t.innerHTML="span.material-icons:first-of-type { margin-left: var(--mdc-list-item-graphic-margin, 32px) !important; margin-right: 0px !important;}",e.shadowRoot.appendChild(t)}))}))}},{key:"_handleClick",value:function(){this.disabled||(this._menu.anchor=this.noAnchor?null:this,this._menu.show())}},{key:"_triggerButton",get:function(){return this.querySelector('ha-icon-button[slot="trigger"], ha-button[slot="trigger"]')}},{key:"_setTriggerAria",value:function(){this._triggerButton&&(this._triggerButton.ariaHasPopup="menu")}}])}(h.WF);v.styles=(0,h.AH)(a||(a=_`
    :host {
      display: inline-block;
      position: relative;
    }
    ::slotted([disabled]) {
      color: var(--disabled-text-color);
    }
  `)),(0,c.__decorate)([(0,u.MZ)()],v.prototype,"corner",void 0),(0,c.__decorate)([(0,u.MZ)({attribute:"menu-corner"})],v.prototype,"menuCorner",void 0),(0,c.__decorate)([(0,u.MZ)({type:Number})],v.prototype,"x",void 0),(0,c.__decorate)([(0,u.MZ)({type:Number})],v.prototype,"y",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"multi",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"activatable",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"disabled",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"fixed",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean,attribute:"no-anchor"})],v.prototype,"noAnchor",void 0),(0,c.__decorate)([(0,u.P)("ha-menu",!0)],v.prototype,"_menu",void 0),v=(0,c.__decorate)([(0,u.EM)("ha-button-menu")],v)},28959:function(e,t,i){i.a(e,(async function(e,s){try{i.r(t),i.d(t,{HaVoiceCommandDialog:function(){return z}});var a=i(61397),n=i(50264),o=i(44734),r=i(56038),l=i(69683),d=i(6454),c=(i(28706),i(74423),i(62062),i(18111),i(61701),i(26099),i(62826)),h=i(96196),u=i(77845),p=i(42256),_=i(92542),v=i(55124),g=(i(17963),i(48206),i(89473)),m=(i(16857),i(95637),i(86451),i(60733),i(56565),i(89600)),f=i(45369),y=i(39396),b=i(62001),k=e([g,m]);[g,m]=k.then?(await k)():k;var x,A,w,M,L,$,C,I,S,B=e=>e,z=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,s=new Array(i),a=0;a<i;a++)s[a]=arguments[a];return(e=(0,l.A)(this,t,[].concat(s)))._opened=!1,e._startListening=!1,e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"showDialog",value:(p=(0,n.A)((0,a.A)().m((function e(t){var i,s;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this._loadPipelines();case 1:s=(null===(i=this._pipelines)||void 0===i?void 0:i.map((e=>e.id)))||[],"preferred"===t.pipeline_id||"last_used"===t.pipeline_id&&!this._pipelineId?this._pipelineId=this._preferredPipeline:["last_used","preferred"].includes(t.pipeline_id)||(this._pipelineId=t.pipeline_id),this._pipelineId&&!s.includes(this._pipelineId)&&(this._pipelineId=this._preferredPipeline),this._startListening=t.start_listening,this._opened=!0;case 2:return e.a(2)}}),e,this)}))),function(e){return p.apply(this,arguments)})},{key:"closeDialog",value:(u=(0,n.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:this._opened=!1,this._pipelines=void 0,(0,_.r)(this,"dialog-closed",{dialog:this.localName});case 1:return e.a(2)}}),e,this)}))),function(){return u.apply(this,arguments)})},{key:"render",value:function(){var e,t,i;return this._opened?(0,h.qy)(x||(x=B`
      <ha-dialog
        open
        @closed=${0}
        .heading=${0}
        flexContent
        hideactions
      >
        <ha-dialog-header slot="heading">
          <ha-icon-button
            slot="navigationIcon"
            dialogAction="cancel"
            .label=${0}
            .path=${0}
          ></ha-icon-button>
          <div slot="title">
            ${0}
            <ha-button-menu
              @opened=${0}
              @closed=${0}
              activatable
              fixed
            >
              <ha-button
                slot="trigger"
                appearance="plain"
                variant="neutral"
                size="small"
              >
                ${0}
                <ha-svg-icon slot="end" .path=${0}></ha-svg-icon>
              </ha-button>
              ${0}
              ${0}
            </ha-button-menu>
          </div>
          <a
            href=${0}
            slot="actionItems"
            target="_blank"
            rel="noopener noreferer"
          >
            <ha-icon-button
              .label=${0}
              .path=${0}
            ></ha-icon-button>
          </a>
        </ha-dialog-header>

        ${0}
      </ha-dialog>
    `),this.closeDialog,this.hass.localize("ui.dialogs.voice_command.title"),this.hass.localize("ui.common.close"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",this.hass.localize("ui.dialogs.voice_command.title"),this._loadPipelines,v.d,null===(e=this._pipeline)||void 0===e?void 0:e.name,"M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z",this._pipelines?null===(t=this._pipelines)||void 0===t?void 0:t.map((e=>(0,h.qy)(w||(w=B`<ha-list-item
                        ?selected=${0}
                        .pipeline=${0}
                        @click=${0}
                        .hasMeta=${0}
                      >
                        ${0}${0}
                      </ha-list-item>`),e.id===this._pipelineId||!this._pipelineId&&e.id===this._preferredPipeline,e.id,this._selectPipeline,e.id===this._preferredPipeline,e.name,e.id===this._preferredPipeline?(0,h.qy)(M||(M=B`
                              <ha-svg-icon
                                slot="meta"
                                .path=${0}
                              ></ha-svg-icon>
                            `),"M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.45,13.97L5.82,21L12,17.27Z"):h.s6))):(0,h.qy)(A||(A=B`<div class="pipelines-loading">
                    <ha-spinner size="small"></ha-spinner>
                  </div>`)),null!==(i=this.hass.user)&&void 0!==i&&i.is_admin?(0,h.qy)(L||(L=B`<li divider role="separator"></li>
                    <a href="/config/voice-assistants/assistants"
                      ><ha-list-item
                        >${0}</ha-list-item
                      ></a
                    >`),this.hass.localize("ui.dialogs.voice_command.manage_assistants")):h.s6,(0,b.o)(this.hass,"/docs/assist/"),this.hass.localize("ui.common.help"),"M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z",this._errorLoadAssist?(0,h.qy)($||($=B`<ha-alert alert-type="error">
              ${0}
            </ha-alert>`),this.hass.localize(`ui.dialogs.voice_command.${this._errorLoadAssist}_error_load_assist`)):this._pipeline?(0,h.qy)(C||(C=B`
                <ha-assist-chat
                  .hass=${0}
                  .pipeline=${0}
                  .startListening=${0}
                >
                </ha-assist-chat>
              `),this.hass,this._pipeline,this._startListening):(0,h.qy)(I||(I=B`<div class="pipelines-loading">
                <ha-spinner size="large"></ha-spinner>
              </div>`))):h.s6}},{key:"willUpdate",value:function(e){(e.has("_pipelineId")||e.has("_opened")&&!0===this._opened&&this._pipelineId)&&this._getPipeline()}},{key:"_loadPipelines",value:(c=(0,n.A)((0,a.A)().m((function e(){var t,i,s;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(!this._pipelines){e.n=1;break}return e.a(2);case 1:return e.n=2,(0,f.nx)(this.hass);case 2:t=e.v,i=t.pipelines,s=t.preferred_pipeline,this._pipelines=i,this._preferredPipeline=s||void 0;case 3:return e.a(2)}}),e,this)}))),function(){return c.apply(this,arguments)})},{key:"_selectPipeline",value:(s=(0,n.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return this._pipelineId=t.currentTarget.pipeline,e.n=1,this.updateComplete;case 1:return e.a(2)}}),e,this)}))),function(e){return s.apply(this,arguments)})},{key:"_getPipeline",value:(i=(0,n.A)((0,a.A)().m((function e(){var t,i,s;return(0,a.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this._pipeline=void 0,this._errorLoadAssist=void 0,t=this._pipelineId,e.p=1,e.n=2,(0,f.mp)(this.hass,t);case 2:i=e.v,t===this._pipelineId&&(this._pipeline=i),e.n=5;break;case 3:if(e.p=3,s=e.v,t===this._pipelineId){e.n=4;break}return e.a(2);case 4:"not_found"===s.code?this._errorLoadAssist="not_found":(this._errorLoadAssist="unknown",console.error(s));case 5:return e.a(2)}}),e,this,[[1,3]])}))),function(){return i.apply(this,arguments)})}],[{key:"styles",get:function(){return[y.nA,(0,h.AH)(S||(S=B`
        ha-dialog {
          --mdc-dialog-max-width: 500px;
          --mdc-dialog-max-height: 500px;
          --dialog-content-padding: 0;
        }
        ha-dialog-header a {
          color: var(--primary-text-color);
        }
        div[slot="title"] {
          display: flex;
          flex-direction: column;
          margin: -4px 0;
        }
        ha-button-menu {
          --mdc-theme-on-primary: var(--text-primary-color);
          --mdc-theme-primary: var(--primary-color);
          margin-top: -8px;
          margin-bottom: 0;
          margin-right: 0;
          margin-inline-end: 0;
          margin-left: -8px;
          margin-inline-start: -8px;
        }
        ha-button-menu ha-button {
          --ha-button-height: 20px;
        }
        ha-button-menu ha-button::part(base) {
          margin-left: 5px;
          padding: 0;
        }
        @media (prefers-color-scheme: dark) {
          ha-button-menu ha-button {
            --ha-button-theme-lighter-color: rgba(255, 255, 255, 0.1);
          }
        }
        ha-button-menu ha-button ha-svg-icon {
          height: 28px;
          margin-left: 4px;
          margin-inline-start: 4px;
          margin-inline-end: initial;
          direction: var(--direction);
        }
        ha-list-item {
          --mdc-list-item-meta-size: 16px;
        }
        ha-list-item ha-svg-icon {
          margin-left: 4px;
          margin-inline-start: 4px;
          margin-inline-end: initial;
          direction: var(--direction);
          display: block;
        }
        ha-button-menu a {
          text-decoration: none;
        }

        .pipelines-loading {
          display: flex;
          justify-content: center;
        }
        ha-assist-chat {
          margin: 0 24px 16px;
          min-height: 399px;
        }
      `))]}}]);var i,s,c,u,p}(h.WF);(0,c.__decorate)([(0,u.MZ)({attribute:!1})],z.prototype,"hass",void 0),(0,c.__decorate)([(0,u.wk)()],z.prototype,"_opened",void 0),(0,c.__decorate)([(0,u.wk)(),(0,p.I)({key:"AssistPipelineId",state:!0,subscribe:!1})],z.prototype,"_pipelineId",void 0),(0,c.__decorate)([(0,u.wk)()],z.prototype,"_pipeline",void 0),(0,c.__decorate)([(0,u.wk)()],z.prototype,"_pipelines",void 0),(0,c.__decorate)([(0,u.wk)()],z.prototype,"_preferredPipeline",void 0),(0,c.__decorate)([(0,u.wk)()],z.prototype,"_errorLoadAssist",void 0),z=(0,c.__decorate)([(0,u.EM)("ha-voice-command-dialog")],z),s()}catch(q){s(q)}}))},12889:function(e,t,i){e.exports=i.p+"12889.161e06a267966b59.js"},72107:function(e,t,i){i(15823)("Int16",(function(e){return function(t,i,s){return e(this,t,i,s)}}))}}]);
//# sourceMappingURL=8004.d4d11559813481a0.js.map