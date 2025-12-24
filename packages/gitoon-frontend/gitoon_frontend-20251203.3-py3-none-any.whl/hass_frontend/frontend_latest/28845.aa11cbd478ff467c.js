export const __webpack_id__="28845";export const __webpack_ids__=["28845"];export const __webpack_modules__={85404:function(e,t,i){i(44114),i(16573),i(78100),i(77936),i(18111),i(61701),i(37467),i(44732),i(79577),i(41549),i(49797),i(49631),i(35623);var a=i(62826),o=i(96196),n=i(44457),s=i(94333),r=i(82286),d=i(69150),l=i(88433),c=i(65063),p=i(74209);i(38962),i(3587),i(75709);class h extends o.WF{willUpdate(e){this.hasUpdated&&!e.has("pipeline")||(this._conversation=[{who:"hass",text:this.hass.localize("ui.dialogs.voice_command.how_can_i_help")}])}firstUpdated(e){super.firstUpdated(e),this.startListening&&this.pipeline&&this.pipeline.stt_engine&&p.N.isSupported&&this._toggleListening(),setTimeout(()=>this._messageInput.focus(),0)}updated(e){super.updated(e),e.has("_conversation")&&this._scrollMessagesBottom()}disconnectedCallback(){super.disconnectedCallback(),this._audioRecorder?.close(),this._unloadAudio()}render(){const e=!!this.pipeline&&(this.pipeline.prefer_local_intents||!this.hass.states[this.pipeline.conversation_engine]||(0,r.$)(this.hass.states[this.pipeline.conversation_engine],l.ZE.CONTROL)),t=p.N.isSupported,i=this.pipeline?.stt_engine&&!this.disableSpeech;return o.qy` <div class="messages"> ${e?o.s6:o.qy` <ha-alert> ${this.hass.localize("ui.dialogs.voice_command.conversation_no_control")} </ha-alert> `} <div class="spacer"></div> ${this._conversation.map(e=>o.qy` <ha-markdown class="message ${(0,s.H)({error:!!e.error,[e.who]:!0})}" breaks cache .content="${e.text}"> </ha-markdown> `)} </div> <div class="input" slot="primaryAction"> <ha-textfield id="message-input" @keyup="${this._handleKeyUp}" @input="${this._handleInput}" .label="${this.hass.localize("ui.dialogs.voice_command.input_label")}" .iconTrailing="${!0}"> <div slot="trailingIcon"> ${this._showSendButton||!i?o.qy` <ha-icon-button class="listening-icon" .path="${"M2,21L23,12L2,3V10L17,12L2,14V21Z"}" @click="${this._handleSendMessage}" .disabled="${this._processing}" .label="${this.hass.localize("ui.dialogs.voice_command.send_text")}"> </ha-icon-button> `:o.qy` ${this._audioRecorder?.active?o.qy` <div class="bouncer"> <div class="double-bounce1"></div> <div class="double-bounce2"></div> </div> `:o.s6} <div class="listening-icon"> <ha-icon-button .path="${"M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"}" @click="${this._handleListeningButton}" .disabled="${this._processing}" .label="${this.hass.localize("ui.dialogs.voice_command.start_listening")}"> </ha-icon-button> ${t?null:o.qy` <ha-svg-icon .path="${"M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"}" class="unsupported"></ha-svg-icon> `} </div> `} </div> </ha-textfield> </div> `}async _scrollMessagesBottom(){const e=this._lastChatMessage;if(e.hasUpdated||await e.updateComplete,this._lastChatMessageImage&&!this._lastChatMessageImage.naturalHeight)try{await this._lastChatMessageImage.decode()}catch(e){console.warn("Failed to decode image:",e)}e.getBoundingClientRect().y<this.getBoundingClientRect().top+24||e.scrollIntoView({behavior:"smooth",block:"start"})}_handleKeyUp(e){const t=e.target;!this._processing&&"Enter"===e.key&&t.value&&(this._processText(t.value),t.value="",this._showSendButton=!1)}_handleInput(e){const t=e.target.value;t&&!this._showSendButton?this._showSendButton=!0:!t&&this._showSendButton&&(this._showSendButton=!1)}_handleSendMessage(){this._messageInput.value&&(this._processText(this._messageInput.value.trim()),this._messageInput.value="",this._showSendButton=!1)}_handleListeningButton(e){e.stopPropagation(),e.preventDefault(),this._toggleListening()}async _toggleListening(){p.N.isSupported?this._audioRecorder?.active?this._stopListening():this._startListening():this._showNotSupportedMessage()}_addMessage(e){this._conversation=[...this._conversation,e]}async _showNotSupportedMessage(){this._addMessage({who:"hass",text:o.qy`${this.hass.localize("ui.dialogs.voice_command.not_supported_microphone_browser")}`})}async _startListening(){this._unloadAudio(),this._processing=!0,this._audioRecorder||(this._audioRecorder=new p.N(e=>{this._audioBuffer?this._audioBuffer.push(e):this._sendAudioChunk(e)})),this._stt_binary_handler_id=void 0,this._audioBuffer=[];const e={who:"user",text:"…"};await this._audioRecorder.start(),this._addMessage(e);const t=this._createAddHassMessageProcessor();try{const i=await(0,d.vU)(this.hass,a=>{if("run-start"===a.type)this._stt_binary_handler_id=a.data.runner_data.stt_binary_handler_id,this._audio=new Audio(a.data.tts_output.url),this._audio.play(),this._audio.addEventListener("ended",()=>{this._unloadAudio(),t.continueConversation&&this._startListening()}),this._audio.addEventListener("pause",this._unloadAudio),this._audio.addEventListener("canplaythrough",()=>this._audio?.play()),this._audio.addEventListener("error",()=>{this._unloadAudio(),(0,c.showAlertDialog)(this,{title:"Error playing audio."})});else if("stt-start"===a.type&&this._audioBuffer){for(const e of this._audioBuffer)this._sendAudioChunk(e);this._audioBuffer=void 0}else"stt-end"===a.type?(this._stt_binary_handler_id=void 0,this._stopListening(),e.text=a.data.stt_output.text,this.requestUpdate("_conversation"),t.addMessage()):a.type.startsWith("intent-")?t.processEvent(a):"run-end"===a.type?(this._stt_binary_handler_id=void 0,i()):"error"===a.type&&(this._unloadAudio(),this._stt_binary_handler_id=void 0,"…"===e.text?(e.text=a.data.message,e.error=!0):t.setError(a.data.message),this._stopListening(),this.requestUpdate("_conversation"),i())},{start_stage:"stt",end_stage:this.pipeline?.tts_engine?"tts":"intent",input:{sample_rate:this._audioRecorder.sampleRate},pipeline:this.pipeline?.id,conversation_id:this._conversationId})}catch(e){await(0,c.showAlertDialog)(this,{title:"Error starting pipeline",text:e.message||e}),this._stopListening()}finally{this._processing=!1}}_stopListening(){if(this._audioRecorder?.stop(),this.requestUpdate("_audioRecorder"),this._stt_binary_handler_id){if(this._audioBuffer)for(const e of this._audioBuffer)this._sendAudioChunk(e);this._sendAudioChunk(new Int16Array),this._stt_binary_handler_id=void 0}this._audioBuffer=void 0}_sendAudioChunk(e){if(this.hass.connection.socket.binaryType="arraybuffer",null==this._stt_binary_handler_id)return;const t=new Uint8Array(1+2*e.length);t[0]=this._stt_binary_handler_id,t.set(new Uint8Array(e.buffer),1),this.hass.connection.socket.send(t)}async _processText(e){this._unloadAudio(),this._processing=!0,this._addMessage({who:"user",text:e});const t=this._createAddHassMessageProcessor();t.addMessage();try{const i=await(0,d.vU)(this.hass,e=>{e.type.startsWith("intent-")&&t.processEvent(e),"intent-end"===e.type&&i(),"error"===e.type&&(t.setError(e.data.message),i())},{start_stage:"intent",input:{text:e},end_stage:"intent",pipeline:this.pipeline?.id,conversation_id:this._conversationId})}catch{t.setError(this.hass.localize("ui.dialogs.voice_command.error"))}finally{this._processing=!1}}_createAddHassMessageProcessor(){let e="";const t=()=>{"…"!==a.hassMessage.text&&(a.hassMessage.text=a.hassMessage.text.substring(0,a.hassMessage.text.length-1),a.hassMessage={who:"hass",text:"…",error:!1},this._addMessage(a.hassMessage))},i={},a={continueConversation:!1,hassMessage:{who:"hass",text:"…",error:!1},addMessage:()=>{this._addMessage(a.hassMessage)},setError:e=>{t(),a.hassMessage.text=e,a.hassMessage.error=!0,this.requestUpdate("_conversation")},processEvent:o=>{if("intent-progress"===o.type&&o.data.chat_log_delta){const n=o.data.chat_log_delta;if(n.role&&(t(),e=n.role),"assistant"===e){if(n.content&&(a.hassMessage.text=a.hassMessage.text.substring(0,a.hassMessage.text.length-1)+n.content+"…",this.requestUpdate("_conversation")),n.tool_calls)for(const e of n.tool_calls)i[e.id]=e}else"tool_result"===e&&i[n.tool_call_id]&&delete i[n.tool_call_id]}else if("intent-end"===o.type){this._conversationId=o.data.intent_output.conversation_id,a.continueConversation=o.data.intent_output.continue_conversation;const e=o.data.intent_output.response.speech?.plain.speech;if(!e)return;"error"===o.data.intent_output.response.response_type?a.setError(e):(a.hassMessage.text=e,this.requestUpdate("_conversation"))}}};return a}constructor(...e){super(...e),this.disableSpeech=!1,this._conversation=[],this._showSendButton=!1,this._processing=!1,this._conversationId=null,this._unloadAudio=()=>{this._audio&&(this._audio.pause(),this._audio.removeAttribute("src"),this._audio=void 0)}}}h.styles=o.AH`
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
      --markdown-list-indent: 1.15em;
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
  `,(0,a.__decorate)([(0,n.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:!1})],h.prototype,"pipeline",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean,attribute:"disable-speech"})],h.prototype,"disableSpeech",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean,attribute:!1})],h.prototype,"startListening",void 0),(0,a.__decorate)([(0,n.P)("#message-input")],h.prototype,"_messageInput",void 0),(0,a.__decorate)([(0,n.P)(".message:last-child")],h.prototype,"_lastChatMessage",void 0),(0,a.__decorate)([(0,n.P)(".message:last-child img:last-of-type")],h.prototype,"_lastChatMessageImage",void 0),(0,a.__decorate)([(0,n.wk)()],h.prototype,"_conversation",void 0),(0,a.__decorate)([(0,n.wk)()],h.prototype,"_showSendButton",void 0),(0,a.__decorate)([(0,n.wk)()],h.prototype,"_processing",void 0),h=(0,a.__decorate)([(0,n.EM)("ha-assist-chat")],h)},69709:function(e,t,i){i(18111),i(22489),i(61701),i(18237);var a=i(62826),o=i(96196),n=i(44457),s=i(1420),r=i(30015),d=i.n(r),l=i(1087),c=(i(14603),i(47566),i(98721),i(2209));let p;var h=i(996);const u=e=>o.qy`${e}`,_=new h.G(1e3),g={reType:/(?<input>(\[!(?<type>caution|important|note|tip|warning)\])(?:\s|\\n)?)/i,typeToHaAlert:{caution:"error",important:"info",note:"info",tip:"success",warning:"warning"}};class m extends o.mN{disconnectedCallback(){if(super.disconnectedCallback(),this.cache){const e=this._computeCacheKey();_.set(e,this.innerHTML)}}createRenderRoot(){return this}update(e){super.update(e),void 0!==this.content&&(this._renderPromise=this._render())}async getUpdateComplete(){return await super.getUpdateComplete(),await this._renderPromise,!0}willUpdate(e){if(!this.innerHTML&&this.cache){const e=this._computeCacheKey();_.has(e)&&((0,o.XX)(u((0,s._)(_.get(e))),this.renderRoot),this._resize())}}_computeCacheKey(){return d()({content:this.content,allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl,breaks:this.breaks})}async _render(){const e=await(async(e,t,a)=>(p||(p=(0,c.LV)(new Worker(new URL(i.p+i.u("55640"),i.b)))),p.renderMarkdown(e,t,a)))(String(this.content),{breaks:this.breaks,gfm:!0},{allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl});(0,o.XX)(u((0,s._)(e.join(""))),this.renderRoot),this._resize();const t=document.createTreeWalker(this,NodeFilter.SHOW_ELEMENT,null);for(;t.nextNode();){const e=t.currentNode;if(e instanceof HTMLAnchorElement&&e.host!==document.location.host)e.target="_blank",e.rel="noreferrer noopener";else if(e instanceof HTMLImageElement)this.lazyImages&&(e.loading="lazy"),e.addEventListener("load",this._resize);else if(e instanceof HTMLQuoteElement){const i=e.firstElementChild?.firstChild?.textContent&&g.reType.exec(e.firstElementChild.firstChild.textContent);if(i){const{type:a}=i.groups,o=document.createElement("ha-alert");o.alertType=g.typeToHaAlert[a.toLowerCase()],o.append(...Array.from(e.childNodes).map(e=>{const t=Array.from(e.childNodes);if(!this.breaks&&t.length){const e=t[0];e.nodeType===Node.TEXT_NODE&&e.textContent===i.input&&e.textContent?.includes("\n")&&(e.textContent=e.textContent.split("\n").slice(1).join("\n"))}return t}).reduce((e,t)=>e.concat(t),[]).filter(e=>e.textContent&&e.textContent!==i.input)),t.parentNode().replaceChild(o,e)}}else e instanceof HTMLElement&&["ha-alert","ha-qr-code","ha-icon","ha-svg-icon"].includes(e.localName)&&i(96175)(`./${e.localName}`)}}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1,this._renderPromise=Promise.resolve(),this._resize=()=>(0,l.r)(this,"content-resize")}}(0,a.__decorate)([(0,n.MZ)()],m.prototype,"content",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:"allow-svg",type:Boolean})],m.prototype,"allowSvg",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:"allow-data-url",type:Boolean})],m.prototype,"allowDataUrl",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],m.prototype,"breaks",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean,attribute:"lazy-images"})],m.prototype,"lazyImages",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],m.prototype,"cache",void 0),m=(0,a.__decorate)([(0,n.EM)("ha-markdown-element")],m)},3587:function(e,t,i){var a=i(62826),o=i(96196),n=i(44457);i(69709);class s extends o.WF{async getUpdateComplete(){const e=await super.getUpdateComplete();return await(this._markdownElement?.updateComplete),e}render(){return this.content?o.qy`<ha-markdown-element .content="${this.content}" .allowSvg="${this.allowSvg}" .allowDataUrl="${this.allowDataUrl}" .breaks="${this.breaks}" .lazyImages="${this.lazyImages}" .cache="${this.cache}"></ha-markdown-element>`:o.s6}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1}}s.styles=o.AH`
    :host {
      display: block;
    }
    ha-markdown-element {
      -ms-user-select: text;
      -webkit-user-select: text;
      -moz-user-select: text;
    }
    ha-markdown-element > *:first-child {
      margin-top: 0;
    }
    ha-markdown-element > *:last-child {
      margin-bottom: 0;
    }
    ha-alert {
      display: block;
      margin: var(--ha-space-1) 0;
    }
    a {
      color: var(--markdown-link-color, var(--primary-color));
    }
    img {
      background-color: var(--markdown-image-background-color);
      border-radius: var(--markdown-image-border-radius);
      max-width: 100%;
    }
    p:first-child > img:first-child {
      vertical-align: top;
    }
    p:first-child > img:last-child {
      vertical-align: top;
    }
    ha-markdown-element > :is(ol, ul) {
      padding-inline-start: var(--markdown-list-indent, revert);
    }
    li {
      &:has(input[type="checkbox"]) {
        list-style: none;
        & > input[type="checkbox"] {
          margin-left: 0;
        }
      }
    }
    svg {
      background-color: var(--markdown-svg-background-color, none);
      color: var(--markdown-svg-color, none);
    }
    code,
    pre {
      background-color: var(--markdown-code-background-color, none);
      border-radius: var(--ha-border-radius-sm);
      color: var(--markdown-code-text-color, inherit);
    }
    code {
      font-size: var(--ha-font-size-s);
      padding: 0.2em 0.4em;
    }
    pre code {
      padding: 0;
    }
    pre {
      padding: var(--ha-space-4);
      overflow: auto;
      line-height: var(--ha-line-height-condensed);
      font-family: var(--ha-font-family-code);
    }
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      line-height: initial;
    }
    h2 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-bold);
    }
    hr {
      border-color: var(--divider-color);
      border-bottom: none;
      margin: var(--ha-space-4) 0;
    }
    table[role="presentation"] {
      --markdown-table-border-collapse: separate;
      --markdown-table-border-width: attr(border, 0);
      --markdown-table-padding-inline: 0;
      --markdown-table-padding-block: 0;
      th {
        vertical-align: attr(align, center);
      }
      td {
        vertical-align: attr(align, left);
      }
    }
    table {
      border-collapse: var(--markdown-table-border-collapse, collapse);
    }
    div:has(> table) {
      overflow: auto;
    }
    th {
      text-align: var(--markdown-table-text-align, start);
    }
    td,
    th {
      border-width: var(--markdown-table-border-width, 1px);
      border-style: var(--markdown-table-border-style, solid);
      border-color: var(--markdown-table-border-color, var(--divider-color));
      padding-inline: var(--markdown-table-padding-inline, 0.5em);
      padding-block: var(--markdown-table-padding-block, 0.25em);
    }
    blockquote {
      border-left: 4px solid var(--divider-color);
      margin-inline: 0;
      padding-inline: 1em;
    }
  `,(0,a.__decorate)([(0,n.MZ)()],s.prototype,"content",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:"allow-svg",type:Boolean})],s.prototype,"allowSvg",void 0),(0,a.__decorate)([(0,n.MZ)({attribute:"allow-data-url",type:Boolean})],s.prototype,"allowDataUrl",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],s.prototype,"breaks",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean,attribute:"lazy-images"})],s.prototype,"lazyImages",void 0),(0,a.__decorate)([(0,n.MZ)({type:Boolean})],s.prototype,"cache",void 0),(0,a.__decorate)([(0,n.P)("ha-markdown-element")],s.prototype,"_markdownElement",void 0),s=(0,a.__decorate)([(0,n.EM)("ha-markdown")],s)},75709:function(e,t,i){i.d(t,{h:()=>l});var a=i(62826),o=i(68846),n=i(92347),s=i(96196),r=i(44457),d=i(63091);class l extends o.J{updated(e){super.updated(e),(e.has("invalid")||e.has("errorMessage"))&&(this.setCustomValidity(this.invalid?this.errorMessage||this.validationMessage||"Invalid":""),(this.invalid||this.validateOnInitialRender||e.has("invalid")&&void 0!==e.get("invalid"))&&this.reportValidity()),e.has("autocomplete")&&(this.autocomplete?this.formElement.setAttribute("autocomplete",this.autocomplete):this.formElement.removeAttribute("autocomplete")),e.has("autocorrect")&&(!1===this.autocorrect?this.formElement.setAttribute("autocorrect","off"):this.formElement.removeAttribute("autocorrect")),e.has("inputSpellcheck")&&(this.inputSpellcheck?this.formElement.setAttribute("spellcheck",this.inputSpellcheck):this.formElement.removeAttribute("spellcheck"))}renderIcon(e,t=!1){const i=t?"trailing":"leading";return s.qy` <span class="mdc-text-field__icon mdc-text-field__icon--${i}" tabindex="${t?1:-1}"> <slot name="${i}Icon"></slot> </span> `}constructor(...e){super(...e),this.icon=!1,this.iconTrailing=!1,this.autocorrect=!0}}l.styles=[n.R,s.AH`.mdc-text-field__input{width:var(--ha-textfield-input-width,100%)}.mdc-text-field:not(.mdc-text-field--with-leading-icon){padding:var(--text-field-padding,0px 16px)}.mdc-text-field__affix--suffix{padding-left:var(--text-field-suffix-padding-left,12px);padding-right:var(--text-field-suffix-padding-right,0px);padding-inline-start:var(--text-field-suffix-padding-left,12px);padding-inline-end:var(--text-field-suffix-padding-right,0px);direction:ltr}.mdc-text-field--with-leading-icon{padding-inline-start:var(--text-field-suffix-padding-left,0px);padding-inline-end:var(--text-field-suffix-padding-right,16px);direction:var(--direction)}.mdc-text-field--with-leading-icon.mdc-text-field--with-trailing-icon{padding-left:var(--text-field-suffix-padding-left,0px);padding-right:var(--text-field-suffix-padding-right,0px);padding-inline-start:var(--text-field-suffix-padding-left,0px);padding-inline-end:var(--text-field-suffix-padding-right,0px)}.mdc-text-field:not(.mdc-text-field--disabled) .mdc-text-field__affix--suffix{color:var(--secondary-text-color)}.mdc-text-field:not(.mdc-text-field--disabled) .mdc-text-field__icon{color:var(--secondary-text-color)}.mdc-text-field__icon--leading{margin-inline-start:16px;margin-inline-end:8px;direction:var(--direction)}.mdc-text-field__icon--trailing{padding:var(--textfield-icon-trailing-padding,12px)}.mdc-floating-label:not(.mdc-floating-label--float-above){max-width:calc(100% - 16px)}.mdc-floating-label--float-above{max-width:calc((100% - 16px)/ .75);transition:none}input{text-align:var(--text-field-text-align,start)}input[type=color]{height:20px}::-ms-reveal{display:none}:host([no-spinner]) input::-webkit-inner-spin-button,:host([no-spinner]) input::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}input[type=color]::-webkit-color-swatch-wrapper{padding:0}:host([no-spinner]) input[type=number]{-moz-appearance:textfield}.mdc-text-field__ripple{overflow:hidden}.mdc-text-field{overflow:var(--text-field-overflow)}.mdc-floating-label{padding-inline-end:16px;padding-inline-start:initial;inset-inline-start:16px!important;inset-inline-end:initial!important;transform-origin:var(--float-start);direction:var(--direction);text-align:var(--float-start);box-sizing:border-box;text-overflow:ellipsis}.mdc-text-field--with-leading-icon.mdc-text-field--filled .mdc-floating-label{max-width:calc(100% - 48px - var(--text-field-suffix-padding-left,0px));inset-inline-start:calc(48px + var(--text-field-suffix-padding-left,0px))!important;inset-inline-end:initial!important;direction:var(--direction)}.mdc-text-field__input[type=number]{direction:var(--direction)}.mdc-text-field__affix--prefix{padding-right:var(--text-field-prefix-padding-right,2px);padding-inline-end:var(--text-field-prefix-padding-right,2px);padding-inline-start:initial}.mdc-text-field:not(.mdc-text-field--disabled) .mdc-text-field__affix--prefix{color:var(--mdc-text-field-label-ink-color)}#helper-text ha-markdown{display:inline-block}`,"rtl"===d.G.document.dir?s.AH`.mdc-floating-label,.mdc-text-field--with-leading-icon,.mdc-text-field--with-leading-icon.mdc-text-field--filled .mdc-floating-label,.mdc-text-field__icon--leading,.mdc-text-field__input[type=number]{direction:rtl;--direction:rtl}`:s.AH``],(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"invalid",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:"error-message"})],l.prototype,"errorMessage",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"icon",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"iconTrailing",void 0),(0,a.__decorate)([(0,r.MZ)()],l.prototype,"autocomplete",void 0),(0,a.__decorate)([(0,r.MZ)({type:Boolean})],l.prototype,"autocorrect",void 0),(0,a.__decorate)([(0,r.MZ)({attribute:"input-spellcheck"})],l.prototype,"inputSpellcheck",void 0),(0,a.__decorate)([(0,r.P)("input")],l.prototype,"formElement",void 0),l=(0,a.__decorate)([(0,r.EM)("ha-textfield")],l)},69150:function(e,t,i){i.d(t,{$$:()=>g,AH:()=>o,NH:()=>h,QC:()=>a,Uc:()=>s,Zr:()=>u,ds:()=>_,hJ:()=>r,mp:()=>l,nx:()=>d,u6:()=>c,vU:()=>n,zn:()=>p});const a=(e,t,i)=>"run-start"===t.type?e={init_options:i,stage:"ready",run:t.data,events:[t],started:new Date(t.timestamp)}:e?((e="wake_word-start"===t.type?{...e,stage:"wake_word",wake_word:{...t.data,done:!1}}:"wake_word-end"===t.type?{...e,wake_word:{...e.wake_word,...t.data,done:!0}}:"stt-start"===t.type?{...e,stage:"stt",stt:{...t.data,done:!1}}:"stt-end"===t.type?{...e,stt:{...e.stt,...t.data,done:!0}}:"intent-start"===t.type?{...e,stage:"intent",intent:{...t.data,done:!1}}:"intent-end"===t.type?{...e,intent:{...e.intent,...t.data,done:!0}}:"tts-start"===t.type?{...e,stage:"tts",tts:{...t.data,done:!1}}:"tts-end"===t.type?{...e,tts:{...e.tts,...t.data,done:!0}}:"run-end"===t.type?{...e,finished:new Date(t.timestamp),stage:"done"}:"error"===t.type?{...e,finished:new Date(t.timestamp),stage:"error",error:t.data}:{...e}).events=[...e.events,t],e):void console.warn("Received unexpected event before receiving session",t),o=(e,t,i)=>{let o;const s=n(e,e=>{o=a(o,e,i),"run-end"!==e.type&&"error"!==e.type||s.then(e=>e()),o&&t(o)},i);return s},n=(e,t,i)=>e.connection.subscribeMessage(t,{...i,type:"assist_pipeline/run"}),s=(e,t)=>e.callWS({type:"assist_pipeline/pipeline_debug/list",pipeline_id:t}),r=(e,t,i)=>e.callWS({type:"assist_pipeline/pipeline_debug/get",pipeline_id:t,pipeline_run_id:i}),d=e=>e.callWS({type:"assist_pipeline/pipeline/list"}),l=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/get",pipeline_id:t}),c=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/create",...t}),p=(e,t,i)=>e.callWS({type:"assist_pipeline/pipeline/update",pipeline_id:t,...i}),h=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/set_preferred",pipeline_id:t}),u=(e,t)=>e.callWS({type:"assist_pipeline/pipeline/delete",pipeline_id:t}),_=e=>e.callWS({type:"assist_pipeline/language/list"}),g=e=>e.callWS({type:"assist_pipeline/device/list"})},88433:function(e,t,i){if(i.d(t,{RW:()=>s,ZE:()=>o,e1:()=>r,vc:()=>n}),59509==i.j)var a=i(44537);var o=function(e){return e[e.CONTROL=1]="CONTROL",e}({});const n=(e,t,i)=>e.callWS({type:"conversation/agent/list",language:t,country:i}),s=(e,t,i,o)=>e.callWS({type:"conversation/agent/homeassistant/debug",sentences:(0,a.e)(t),language:i,device_id:o}),r=(e,t,i)=>e.callWS({type:"conversation/agent/homeassistant/language_scores",language:t,country:i})},74209:function(e,t,i){i.d(t,{N:()=>a});i(14603),i(47566),i(98721);class a{get active(){return this._active}get sampleRate(){return this._context?.sampleRate}static get isSupported(){return window.isSecureContext&&(window.AudioContext||window.webkitAudioContext)}async start(){if(this._context&&this._stream&&this._source&&this._recorder)this._stream.getTracks()[0].enabled=!0,await this._context.resume(),this._active=!0;else try{await this._createContext()}catch(e){console.error(e),this._active=!1}}async stop(){this._active=!1,this._stream&&(this._stream.getTracks()[0].enabled=!1),await(this._context?.suspend())}close(){this._active=!1,this._stream?.getTracks()[0].stop(),this._recorder&&(this._recorder.port.onmessage=null),this._source?.disconnect(),this._context?.close(),this._stream=void 0,this._source=void 0,this._recorder=void 0,this._context=void 0}async _createContext(){const e=new(AudioContext||webkitAudioContext);this._stream=await navigator.mediaDevices.getUserMedia({audio:!0}),await e.audioWorklet.addModule(new URL(i.p+i.u("33921"),i.b)),this._context=e,this._source=this._context.createMediaStreamSource(this._stream),this._recorder=new AudioWorkletNode(this._context,"recorder-worklet"),this._recorder.port.onmessage=e=>{this._active&&this._callback(e.data)},this._active=!0,this._source.connect(this._recorder)}constructor(e){this._active=!1,this._callback=e}}},996:function(e,t,i){i.d(t,{G:()=>a});class a{get(e){return this._cache.get(e)}set(e,t){this._cache.set(e,t),this._expiration&&window.setTimeout(()=>this._cache.delete(e),this._expiration)}has(e){return this._cache.has(e)}constructor(e){this._cache=new Map,this._expiration=e}}},96175:function(e,t,i){var a={"./ha-icon-prev":["89133","61982"],"./ha-icon-button-toolbar":["9882","26431","76775"],"./ha-alert":["38962","19695"],"./ha-icon-button-toggle":["62501","77254"],"./ha-svg-icon.ts":["67094"],"./ha-alert.ts":["38962","19695"],"./ha-icon":["88945","51146"],"./ha-icon-next.ts":["43661","63902"],"./ha-qr-code.ts":["60543","51343","62740"],"./ha-icon-overflow-menu.ts":["75248","46095","26431","22016","56297"],"./ha-icon-button-toggle.ts":["62501","77254"],"./ha-icon-button-group":["39826","13647"],"./ha-svg-icon":["67094"],"./ha-icon-button-prev":["45100","99197"],"./ha-icon-button.ts":["26300"],"./ha-icon-overflow-menu":["75248","46095","26431","22016","56297"],"./ha-icon-button-arrow-next":["99028","54101"],"./ha-icon-button-prev.ts":["45100","99197"],"./ha-icon-picker":["64138","44533","7199","46095","48654","72991"],"./ha-icon-button-toolbar.ts":["9882","26431","76775"],"./ha-icon-button-arrow-prev.ts":["90248","17041"],"./ha-icon-button-next":["25440","81049"],"./ha-icon-next":["43661","63902"],"./ha-icon-picker.ts":["64138","44533","7199","46095","48654","72991"],"./ha-icon-prev.ts":["89133","61982"],"./ha-icon-button-arrow-prev":["90248","17041"],"./ha-icon-button-next.ts":["25440","81049"],"./ha-icon.ts":["88945","51146"],"./ha-qr-code":["60543","51343","62740"],"./ha-icon-button":["26300"],"./ha-icon-button-group.ts":["39826","13647"],"./ha-icon-button-arrow-next.ts":["99028","54101"]};function o(e){if(!i.o(a,e))return Promise.resolve().then(function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t});var t=a[e],o=t[0];return Promise.all(t.slice(1).map(i.e)).then(function(){return i(o)})}o.keys=()=>Object.keys(a),o.id=96175,e.exports=o}};
//# sourceMappingURL=28845.aa11cbd478ff467c.js.map