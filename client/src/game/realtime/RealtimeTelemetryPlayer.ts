/**
 * 实时遥测播放器
 * 通过 WebSocket 接收后端实时数据
 */

export interface TelemetryObject {
  id: string;
  type: string;
  name: string;
  color: string;
  longitude: number;
  latitude: number;
  altitude: number;
  heading: number;
  speed?: number;
  fuelPercent?: number;
}

export interface TelemetryFrame {
  timestamp: number;
  relativeTime: number;
  step: number;
  objects: TelemetryObject[];
}

export type TelemetryCallback = (frame: TelemetryFrame) => void;

class RealtimeTelemetryPlayer {
  private ws: WebSocket | null = null;
  private connected: boolean = false;
  private frameCallbacks: TelemetryCallback[] = [];
  private statusCallbacks: ((connected: boolean) => void)[] = [];
  private currentFrame: TelemetryFrame | null = null;
  private frameCount: number = 0;
  private reconnectTimer: number | null = null;
  private wsUrl: string = '';

  /**
   * 连接到 WebSocket 服务器
   */
  connect(url: string): void {
    if (this.ws) {
      this.disconnect();
    }

    this.wsUrl = url;
    console.log(`[RealtimeTelemetry] 连接到: ${url}`);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[RealtimeTelemetry] 已连接');
        this.connected = true;
        this.notifyStatusCallbacks(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const frame: TelemetryFrame = JSON.parse(event.data);
          this.currentFrame = frame;
          this.frameCount++;
          this.notifyFrameCallbacks(frame);
        } catch (e) {
          console.error('[RealtimeTelemetry] 解析数据失败:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('[RealtimeTelemetry] 连接关闭');
        this.connected = false;
        this.notifyStatusCallbacks(false);
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('[RealtimeTelemetry] 连接错误:', error);
        this.connected = false;
        this.notifyStatusCallbacks(false);
      };
    } catch (e) {
      console.error('[RealtimeTelemetry] 创建连接失败:', e);
      this.scheduleReconnect();
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connected = false;
    this.notifyStatusCallbacks(false);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = window.setTimeout(() => {
      if (this.wsUrl && !this.connected) {
        console.log('[RealtimeTelemetry] 尝试重连...');
        this.connect(this.wsUrl);
      }
    }, 3000);
  }

  /**
   * 注册帧数据回调
   */
  onFrame(callback: TelemetryCallback): void {
    this.frameCallbacks.push(callback);
  }

  /**
   * 移除帧数据回调
   */
  offFrame(callback: TelemetryCallback): void {
    this.frameCallbacks = this.frameCallbacks.filter(cb => cb !== callback);
  }

  /**
   * 注册连接状态回调
   */
  onStatus(callback: (connected: boolean) => void): void {
    this.statusCallbacks.push(callback);
  }

  /**
   * 移除连接状态回调
   */
  offStatus(callback: (connected: boolean) => void): void {
    this.statusCallbacks = this.statusCallbacks.filter(cb => cb !== callback);
  }

  /**
   * 通知帧数据回调
   */
  private notifyFrameCallbacks(frame: TelemetryFrame): void {
    for (const callback of this.frameCallbacks) {
      try {
        callback(frame);
      } catch (e) {
        console.error('[RealtimeTelemetry] 回调执行失败:', e);
      }
    }
  }

  /**
   * 通知连接状态回调
   */
  private notifyStatusCallbacks(connected: boolean): void {
    for (const callback of this.statusCallbacks) {
      try {
        callback(connected);
      } catch (e) {
        console.error('[RealtimeTelemetry] 状态回调执行失败:', e);
      }
    }
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.connected;
  }

  /**
   * 获取当前帧
   */
  getCurrentFrame(): TelemetryFrame | null {
    return this.currentFrame;
  }

  /**
   * 获取帧计数
   */
  getFrameCount(): number {
    return this.frameCount;
  }

  /**
   * 重置
   */
  reset(): void {
    this.disconnect();
    this.currentFrame = null;
    this.frameCount = 0;
  }
}

export default RealtimeTelemetryPlayer;
