<template>
  <div class="emoji-viewer">
    <el-card class="emoji-container" shadow="always">
      <template #header>
        <div class="card-header">
          <h2>😊 Emoji 查看器</h2>
          <div class="header-actions">
            <el-tag type="info">总共有 {{ allEmojis.length }} 个表情</el-tag>
            <el-button @click="toggleDarkMode" :icon="isDarkMode ? Sunny : Moon" circle size="small" />
          </div>
        </div>
      </template>

      <!-- 搜索和过滤 -->
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索表情符号..."
          :prefix-icon="Search"
          clearable
          size="large"
          class="search-input"
        >
          <template #append>
            <el-button @click="clearSearch" :icon="Close" :disabled="!searchQuery"> 清除 </el-button>
          </template>
        </el-input>

        <div class="filter-section">
          <el-select v-model="selectedCategory" placeholder="选择分类" clearable size="large" class="category-select">
            <el-option
              v-for="category in categories"
              :key="category.value"
              :label="category.label"
              :value="category.value"
            >
              <span style="float: left">{{ category.label }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px"> {{ category.count }} 个 </span>
            </el-option>
          </el-select>

          <el-select v-model="skinTone" placeholder="肤色" size="large" class="skin-tone-select">
            <el-option label="默认" value="default" />
            <el-option label="浅色" value="light" />
            <el-option label="中浅色" value="medium-light" />
            <el-option label="中等色" value="medium" />
            <el-option label="中深色" value="medium-dark" />
            <el-option label="深色" value="dark" />
          </el-select>
        </div>
      </div>

      <!-- 复制历史 -->
      <div v-if="copyHistory.length > 0" class="copy-history">
        <div class="history-header">
          <span>📋 复制历史</span>
          <el-button @click="clearHistory" :icon="Delete" size="small" type="danger" text> 清空历史 </el-button>
        </div>
        <div class="history-items">
          <el-tag
            v-for="(item, index) in copyHistory.slice(-10)"
            :key="index"
            @click="copyToClipboard(item.emoji)"
            class="history-item"
            :title="item.name"
          >
            {{ item.emoji }}
          </el-tag>
        </div>
      </div>

      <el-divider />

      <!-- 统计信息 -->
      <div class="stats-section">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="总数量">
            <el-tag type="info">{{ allEmojis.length }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前显示">
            <el-tag type="success">{{ filteredEmojis.length }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="已复制">
            <el-tag type="warning">{{ totalCopied }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="收藏数量">
            <el-tag type="danger">{{ favorites.length }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider />

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- Emoji网格 -->
      <div v-else class="emoji-grid">
        <div
          v-for="emoji in paginatedEmojis"
          :key="emoji.emoji"
          class="emoji-item"
          :class="{
            favorite: isFavorite(emoji.emoji),
            copied: recentlyCopied === emoji.emoji
          }"
          @click="copyToClipboard(emoji.emoji, emoji.name)"
          @contextmenu.prevent="showContextMenu(emoji, $event)"
        >
          <div class="emoji-display">{{ emoji.emoji }}</div>
          <div class="emoji-name">{{ emoji.name }}</div>
          <div class="emoji-actions">
            <el-button
              @click.stop="toggleFavorite(emoji.emoji)"
              :icon="isFavorite(emoji.emoji) ? StarFilled : Star"
              circle
              size="small"
              :type="isFavorite(emoji.emoji) ? 'danger' : 'default'"
            />
            <el-button @click.stop="showEmojiDetail(emoji)" :icon="InfoFilled" circle size="small" type="primary" />
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[50, 100, 200, 500]"
          :total="filteredEmojis.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- Emoji详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="表情详情" width="500px">
      <div v-if="selectedEmoji" class="emoji-detail">
        <div class="detail-emoji">{{ selectedEmoji.emoji }}</div>
        <div class="detail-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="名称">
              {{ selectedEmoji.name }}
            </el-descriptions-item>
            <el-descriptions-item label="Unicode">
              <el-input :value="selectedEmoji.unicode" readonly size="small">
                <template #append>
                  <el-button @click="copyToClipboard(selectedEmoji.unicode)" size="small"> 复制 </el-button>
                </template>
              </el-input>
            </el-descriptions-item>
            <el-descriptions-item label="分类">
              <el-tag>{{ getCategoryLabel(selectedEmoji.category) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="关键词">
              <el-tag v-for="keyword in selectedEmoji.keywords" :key="keyword" size="small" class="keyword-tag">
                {{ keyword }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="copyToClipboard(selectedEmoji!.emoji, selectedEmoji!.name)">
          复制表情
        </el-button>
      </template>
    </el-dialog>

    <!-- 右键菜单 -->
    <el-dropdown ref="contextMenu" :show="contextMenuVisible" @command="handleContextMenuCommand" trigger="contextmenu">
      <span></span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="copy" :icon="CopyDocument"> 复制表情 </el-dropdown-item>
          <el-dropdown-item command="copy-unicode" :icon="Document"> 复制Unicode </el-dropdown-item>
          <el-dropdown-item command="favorite" :icon="Star">
            {{ contextEmoji?.emoji && isFavorite(contextEmoji.emoji) ? '取消收藏' : '添加收藏' }}
          </el-dropdown-item>
          <el-dropdown-item command="detail" :icon="InfoFilled"> 查看详情 </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import {
    Search,
    Close,
    Delete,
    Star,
    StarFilled,
    InfoFilled,
    CopyDocument,
    Document,
    Moon,
    Sunny
  } from '@element-plus/icons-vue'

  // Emoji数据接口
  interface Emoji {
    emoji: string
    name: string
    unicode: string
    category: string
    keywords: string[]
  }

  interface CopyHistory {
    emoji: string
    name: string
    timestamp: number
  }

  // 响应式数据
  const searchQuery = ref('')
  const selectedCategory = ref('')
  const skinTone = ref('default')
  const currentPage = ref(1)
  const pageSize = ref(100)
  const loading = ref(false)
  const detailDialogVisible = ref(false)
  const selectedEmoji = ref<Emoji | null>(null)
  const copyHistory = ref<CopyHistory[]>([])
  const favorites = ref<string[]>([])
  const recentlyCopied = ref('')
  const contextMenuVisible = ref(false)
  const contextEmoji = ref<Emoji | null>(null)
  const isDarkMode = ref(false)

  // 完整的Emoji数据库
  const allEmojis = ref<Emoji[]>([
    // 面部表情
    { emoji: '😀', name: '笑脸', unicode: 'U+1F600', category: 'faces', keywords: ['开心', '笑', 'happy'] },
    { emoji: '😃', name: '大笑脸', unicode: 'U+1F603', category: 'faces', keywords: ['大笑', '开心', 'smile'] },
    { emoji: '😄', name: '笑眼脸', unicode: 'U+1F604', category: 'faces', keywords: ['笑眼', '开心', 'grin'] },
    { emoji: '😁', name: '眯眼笑', unicode: 'U+1F601', category: 'faces', keywords: ['眯眼', '微笑', 'beam'] },
    { emoji: '😅', name: '尴尬笑', unicode: 'U+1F605', category: 'faces', keywords: ['尴尬', '冷汗', 'sweat'] },
    { emoji: '😂', name: '笑哭脸', unicode: 'U+1F602', category: 'faces', keywords: ['笑哭', '眼泪', 'joy'] },
    { emoji: '🤣', name: '大笑哭脸', unicode: 'U+1F923', category: 'faces', keywords: ['大笑', '哭笑', 'rofl'] },
    { emoji: '😊', name: '害羞脸', unicode: 'U+1F60A', category: 'faces', keywords: ['害羞', '脸红', 'blush'] },
    { emoji: '😇', name: '天使脸', unicode: 'U+1F607', category: 'faces', keywords: ['天使', '光环', 'angel'] },
    { emoji: '🙂', name: '微笑脸', unicode: 'U+1F642', category: 'faces', keywords: ['微笑', '满意', 'slight'] },
    { emoji: '😉', name: '眨眼脸', unicode: 'U+1F609', category: 'faces', keywords: ['眨眼', '调皮', 'wink'] },
    { emoji: '😌', name: '满足脸', unicode: 'U+1F60C', category: 'faces', keywords: ['满足', '轻松', 'relieved'] },
    { emoji: '😍', name: '爱慕脸', unicode: 'U+1F60D', category: 'faces', keywords: ['爱慕', '喜欢', 'love'] },
    { emoji: '🥰', name: '爱心脸', unicode: 'U+1F970', category: 'faces', keywords: ['爱心', '恋爱', 'hearts'] },
    { emoji: '😘', name: '亲吻脸', unicode: 'U+1F618', category: 'faces', keywords: ['亲吻', '飞吻', 'kiss'] },
    { emoji: '😗', name: '嘟嘴脸', unicode: 'U+1F617', category: 'faces', keywords: ['嘟嘴', '亲吻', 'kissing'] },
    { emoji: '😙', name: '微笑亲吻', unicode: 'U+1F619', category: 'faces', keywords: ['微笑', '亲吻', 'kissing'] },
    { emoji: '😚', name: '闭眼亲吻', unicode: 'U+1F61A', category: 'faces', keywords: ['闭眼', '亲吻', 'kissing'] },
    { emoji: '😋', name: '美味脸', unicode: 'U+1F60B', category: 'faces', keywords: ['美味', '舔嘴', 'yum'] },
    { emoji: '😛', name: '吐舌头', unicode: 'U+1F61B', category: 'faces', keywords: ['吐舌', '调皮', 'tongue'] },
    { emoji: '😜', name: '眨眼吐舌', unicode: 'U+1F61C', category: 'faces', keywords: ['眨眼', '吐舌', 'wink'] },
    { emoji: '🤪', name: '狂野脸', unicode: 'U+1F92A', category: 'faces', keywords: ['狂野', '疯狂', 'zany'] },
    { emoji: '😝', name: '眯眼吐舌', unicode: 'U+1F61D', category: 'faces', keywords: ['眯眼', '吐舌', 'squint'] },
    { emoji: '🤑', name: '金钱脸', unicode: 'U+1F911', category: 'faces', keywords: ['金钱', '贪婪', 'money'] },
    { emoji: '🤗', name: '拥抱脸', unicode: 'U+1F917', category: 'faces', keywords: ['拥抱', '温暖', 'hug'] },
    { emoji: '🤭', name: '捂嘴脸', unicode: 'U+1F92D', category: 'faces', keywords: ['捂嘴', '秘密', 'hand'] },
    { emoji: '🤫', name: '嘘脸', unicode: 'U+1F92B', category: 'faces', keywords: ['嘘', '安静', 'shushing'] },
    { emoji: '🤔', name: '思考脸', unicode: 'U+1F914', category: 'faces', keywords: ['思考', '沉思', 'thinking'] },
    { emoji: '🤐', name: '闭嘴脸', unicode: 'U+1F910', category: 'faces', keywords: ['闭嘴', '拉链', 'zipper'] },
    { emoji: '🤨', name: '无脸', unicode: 'U+1F928', category: 'faces', keywords: ['无脸', '面无表情', 'no'] },
    { emoji: '😐', name: '中性脸', unicode: 'U+1F610', category: 'faces', keywords: ['中性', '无表情', 'neutral'] },
    {
      emoji: '😑',
      name: '无语脸',
      unicode: 'U+1F611',
      category: 'faces',
      keywords: ['无语', '平静', 'expressionless']
    },
    { emoji: '😶', name: '沉默脸', unicode: 'U+1F636', category: 'faces', keywords: ['沉默', '闭嘴', 'mute'] },
    { emoji: '😏', name: '得意脸', unicode: 'U+1F60F', category: 'faces', keywords: ['得意', '奸笑', 'smirk'] },
    { emoji: '😒', name: '不爽脸', unicode: 'U+1F612', category: 'faces', keywords: ['不爽', '鄙视', 'unamused'] },
    { emoji: '🙄', name: '翻白眼', unicode: 'U+1F644', category: 'faces', keywords: ['翻白眼', '无语', 'roll'] },
    { emoji: '😬', name: '尴尬脸', unicode: 'U+1F62C', category: 'faces', keywords: ['尴尬', '紧张', 'grimace'] },
    { emoji: '😮', name: '惊讶脸', unicode: 'U+1F62E', category: 'faces', keywords: ['惊讶', '张嘴', 'open'] },
    { emoji: '😯', name: '静默惊讶', unicode: 'U+1F62F', category: 'faces', keywords: ['惊讶', '静默', 'hushed'] },
    { emoji: '😲', name: '震惊脸', unicode: 'U+1F632', category: 'faces', keywords: ['震惊', '惊呆', 'astonished'] },
    { emoji: '😳', name: '脸红脸', unicode: 'U+1F633', category: 'faces', keywords: ['脸红', '害羞', 'flushed'] },
    { emoji: '🥺', name: '恳求脸', unicode: 'U+1F97A', category: 'faces', keywords: ['恳求', '可怜', 'pleading'] },
    { emoji: '😥', name: '失望脸', unicode: 'U+1F625', category: 'faces', keywords: ['失望', '沮丧', 'disappointed'] },
    { emoji: '😢', name: '哭脸', unicode: 'U+1F622', category: 'faces', keywords: ['哭', '眼泪', 'cry'] },
    { emoji: '😭', name: '大哭脸', unicode: 'U+1F62D', category: 'faces', keywords: ['大哭', '泪流满面', 'sob'] },
    { emoji: '😱', name: '恐惧脸', unicode: 'U+1F631', category: 'faces', keywords: ['恐惧', '害怕', 'scream'] },
    { emoji: '😖', name: '困惑脸', unicode: 'U+1F616', category: 'faces', keywords: ['困惑', '纠结', 'confounded'] },
    { emoji: '😣', name: '痛苦脸', unicode: 'U+1F623', category: 'faces', keywords: ['痛苦', '挣扎', 'persevere'] },
    { emoji: '😞', name: '沮丧脸', unicode: 'U+1F61E', category: 'faces', keywords: ['沮丧', '失望', 'disappointed'] },
    { emoji: '😓', name: '流汗脸', unicode: 'U+1F613', category: 'faces', keywords: ['流汗', '紧张', 'sweat'] },
    { emoji: '😩', name: '疲惫脸', unicode: 'U+1F629', category: 'faces', keywords: ['疲惫', '疲倦', 'weary'] },
    { emoji: '😫', name: '痛苦呻吟', unicode: 'U+1F62B', category: 'faces', keywords: ['痛苦', '呻吟', 'tired'] },
    { emoji: '🥱', name: '打哈欠', unicode: 'U+1F971', category: 'faces', keywords: ['哈欠', '困倦', 'yawning'] },
    { emoji: '😪', name: '睡觉脸', unicode: 'U+1F62A', category: 'faces', keywords: ['睡觉', '困', 'sleeping'] },
    { emoji: '😴', name: '熟睡脸', unicode: 'U+1F634', category: 'faces', keywords: ['熟睡', '打鼾', 'sleeping'] },
    { emoji: '😷', name: '口罩脸', unicode: 'U+1F637', category: 'faces', keywords: ['口罩', '生病', 'mask'] },
    { emoji: '🤒', name: '发烧脸', unicode: 'U+1F912', category: 'faces', keywords: ['发烧', '温度计', 'thermometer'] },
    { emoji: '🤕', name: '受伤脸', unicode: 'U+1F915', category: 'faces', keywords: ['受伤', '绷带', 'injury'] },
    { emoji: '🤢', name: '恶心脸', unicode: 'U+1F922', category: 'faces', keywords: ['恶心', '呕吐', 'nauseated'] },
    { emoji: '🤮', name: '呕吐脸', unicode: 'U+1F92E', category: 'faces', keywords: ['呕吐', '恶心', 'vomiting'] },
    { emoji: '🤧', name: '打喷嚏', unicode: 'U+1F927', category: 'faces', keywords: ['喷嚏', '感冒', 'sneezing'] },
    { emoji: '😵', name: '眩晕脸', unicode: 'U+1F635', category: 'faces', keywords: ['眩晕', '晕倒', 'dizzy'] },
    { emoji: '🤯', name: '爆炸头', unicode: 'U+1F92F', category: 'faces', keywords: ['爆炸', '震惊', 'exploding'] },
    { emoji: '🤠', name: '牛仔脸', unicode: 'U+1F920', category: 'faces', keywords: ['牛仔', '帽子', 'cowboy'] },
    { emoji: '🥳', name: '派对脸', unicode: 'U+1F973', category: 'faces', keywords: ['派对', '庆祝', 'partying'] },
    { emoji: '😎', name: '墨镜脸', unicode: 'U+1F60E', category: 'faces', keywords: ['墨镜', '酷', 'cool'] },
    { emoji: '🤓', name: '书呆子脸', unicode: 'U+1F913', category: 'faces', keywords: ['书呆子', '眼镜', 'nerd'] },
    { emoji: '🧐', name: '单片眼镜', unicode: 'U+1F9D0', category: 'faces', keywords: ['单片镜', '观察', 'monocle'] },
    { emoji: '😕', name: '困惑脸', unicode: 'U+1F615', category: 'faces', keywords: ['困惑', '迷惑', 'confused'] },
    { emoji: '😟', name: '担心脸', unicode: 'U+1F61F', category: 'faces', keywords: ['担心', '焦虑', 'worried'] },
    { emoji: '🙁', name: '微皱眉', unicode: 'U+1F641', category: 'faces', keywords: ['皱眉', '不高兴', 'frown'] },
    { emoji: '😔', name: '沉思脸', unicode: 'U+1F614', category: 'faces', keywords: ['沉思', '悲伤', 'pensive'] },
    { emoji: '😪', name: '困倦脸', unicode: 'U+1F62A', category: 'faces', keywords: ['困倦', '想睡', 'sleepy'] },
    { emoji: '🤤', name: '流口水', unicode: 'U+1F924', category: 'faces', keywords: ['口水', '流涎', 'drooling'] },
    { emoji: '😴', name: '打鼾', unicode: 'U+1F634', category: 'faces', keywords: ['打鼾', '睡觉', 'sleeping'] },

    // 手势符号
    { emoji: '👍', name: '大拇指', unicode: 'U+1F44D', category: 'gestures', keywords: ['赞', '好', 'thumb'] },
    { emoji: '👎', name: '大拇指向下', unicode: 'U+1F44E', category: 'gestures', keywords: ['踩', '差', 'down'] },
    { emoji: '👌', name: 'OK手势', unicode: 'U+1F44C', category: 'gestures', keywords: ['OK', '好的', 'okay'] },
    { emoji: '✌️', name: '胜利手势', unicode: 'U+270C', category: 'gestures', keywords: ['胜利', '和平', 'peace'] },
    { emoji: '🤞', name: '交叉手指', unicode: 'U+1F91E', category: 'gestures', keywords: ['祈祷', '幸运', 'crossed'] },
    { emoji: '🤟', name: '举手', unicode: 'U+1F91F', category: 'gestures', keywords: ['举手', '高举手', 'raised'] },
    { emoji: '🤘', name: '摇滚手势', unicode: 'U+1F918', category: 'gestures', keywords: ['摇滚', '酷', 'rock'] },
    { emoji: '🤙', name: '打电话手势', unicode: 'U+1F919', category: 'gestures', keywords: ['打电话', '电话', 'call'] },
    { emoji: '👈', name: '左指', unicode: 'U+1F448', category: 'gestures', keywords: ['左指', '左边', 'left'] },
    { emoji: '👉', name: '右指', unicode: 'U+1F449', category: 'gestures', keywords: ['右指', '右边', 'right'] },
    { emoji: '👆', name: '上指', unicode: 'U+1F446', category: 'gestures', keywords: ['上指', '上面', 'up'] },
    { emoji: '👇', name: '下指', unicode: 'U+1F447', category: 'gestures', keywords: ['下指', '下面', 'down'] },
    { emoji: '☝️', name: '食指上指', unicode: 'U+261D', category: 'gestures', keywords: ['指点', '注意', 'point'] },
    { emoji: '✋', name: '举手', unicode: 'U+270B', category: 'gestures', keywords: ['举手', '停下', 'hand'] },
    { emoji: '🤚', name: '手背', unicode: 'U+1F91A', category: 'gestures', keywords: ['手背', '停止', 'back'] },
    { emoji: '🖐️', name: '张开手掌', unicode: 'U+1F590', category: 'gestures', keywords: ['手掌', '张开', 'open'] },
    {
      emoji: '🖖',
      name: '瓦肯举手',
      unicode: 'U+1F596',
      category: 'gestures',
      keywords: ['瓦肯', '星际迷航', 'vulcan']
    },
    { emoji: '👋', name: '挥手', unicode: 'U+1F44B', category: 'gestures', keywords: ['挥手', '再见', 'wave'] },
    { emoji: '🤏', name: '捏手指', unicode: 'U+1F90F', category: 'gestures', keywords: ['捏指', '意大利', 'pinched'] },
    { emoji: '✍️', name: '写字', unicode: 'U+270D', category: 'gestures', keywords: ['写字', '记录', 'writing'] },
    { emoji: '🙌', name: '举双手', unicode: 'U+1F64C', category: 'gestures', keywords: ['举手', '庆祝', 'raised'] },
    { emoji: '👐', name: '张开双手', unicode: 'U+1F450', category: 'gestures', keywords: ['张开', '拥抱', 'open'] },
    { emoji: '🤲', name: '手心向上', unicode: 'U+1F932', category: 'gestures', keywords: ['手心', '捧着', 'palms'] },
    { emoji: '🙏', name: '祈祷', unicode: 'U+1F64F', category: 'gestures', keywords: ['祈祷', '感谢', 'folded'] },
    { emoji: '🤝', name: '握手', unicode: 'U+1F91D', category: 'gestures', keywords: ['握手', '合作', 'handshake'] },
    { emoji: '💪', name: '肌肉', unicode: 'U+1F4AA', category: 'gestures', keywords: ['肌肉', '力量', 'flexed'] },

    // 动物
    { emoji: '🐶', name: '小狗', unicode: 'U+1F415', category: 'animals', keywords: ['狗', '宠物', 'dog'] },
    { emoji: '🐱', name: '小猫', unicode: 'U+1F408', category: 'animals', keywords: ['猫', '宠物', 'cat'] },
    { emoji: '🐭', name: '老鼠', unicode: 'U+1F42D', category: 'animals', keywords: ['老鼠', '啮齿', 'mouse'] },
    { emoji: '🐹', name: '仓鼠', unicode: 'U+1F439', category: 'animals', keywords: ['仓鼠', '宠物', 'hamster'] },
    { emoji: '🐰', name: '兔子', unicode: 'U+1F430', category: 'animals', keywords: ['兔子', '可爱', 'rabbit'] },
    { emoji: '🦊', name: '狐狸', unicode: 'U+1F98A', category: 'animals', keywords: ['狐狸', '狡猾', 'fox'] },
    { emoji: '🐻', name: '熊', unicode: 'U+1F43B', category: 'animals', keywords: ['熊', '大型动物', 'bear'] },
    { emoji: '🐼', name: '熊猫', unicode: 'U+1F3C3', category: 'animals', keywords: ['熊猫', '国宝', 'panda'] },
    { emoji: '🐨', name: '考拉', unicode: 'U+1F428', category: 'animals', keywords: ['考拉', '澳洲', 'koala'] },
    { emoji: '🐯', name: '老虎', unicode: 'U+1F42F', category: 'animals', keywords: ['老虎', '大型猫科', 'tiger'] },
    { emoji: '🦁', name: '狮子', unicode: 'U+1F981', category: 'animals', keywords: ['狮子', '百兽之王', 'lion'] },
    { emoji: '🐮', name: '牛', unicode: 'U+1F42E', category: 'animals', keywords: ['牛', '牲畜', 'cow'] },
    { emoji: '🐷', name: '猪', unicode: 'U+1F437', category: 'animals', keywords: ['猪', '家畜', 'pig'] },
    { emoji: '🐸', name: '青蛙', unicode: 'U+1F438', category: 'animals', keywords: ['青蛙', '两栖', 'frog'] },
    { emoji: '🐵', name: '猴子', unicode: 'U+1F435', category: 'animals', keywords: ['猴子', '灵长类', 'monkey'] },
    { emoji: '🦄', name: '独角兽', unicode: 'U+1F984', category: 'animals', keywords: ['独角兽', '神话', 'unicorn'] },
    { emoji: '🐴', name: '马', unicode: 'U+1F434', category: 'animals', keywords: ['马', '奔跑', 'horse'] },
    { emoji: '🦓', name: '斑马', unicode: 'U+1F993', category: 'animals', keywords: ['斑马', '条纹', 'zebra'] },
    { emoji: '🦌', name: '鹿', unicode: 'U+1F98C', category: 'animals', keywords: ['鹿', '森林', 'deer'] },
    { emoji: '🦒', name: '长颈鹿', unicode: 'U+1F992', category: 'animals', keywords: ['长颈鹿', '脖子长', 'giraffe'] },
    { emoji: '🐘', name: '大象', unicode: 'U+1F418', category: 'animals', keywords: ['大象', '长鼻子', 'elephant'] },
    { emoji: '🦏', name: '犀牛', unicode: 'U+1F98F', category: 'animals', keywords: ['犀牛', '角', 'rhinoceros'] },
    { emoji: '🦛', name: '河马', unicode: 'U+1F99B', category: 'animals', keywords: ['河马', '大嘴', 'hippopotamus'] },
    { emoji: '🐪', name: '骆驼', unicode: 'U+1F42A', category: 'animals', keywords: ['骆驼', '沙漠', 'dromedary'] },
    { emoji: '🐫', name: '双峰驼', unicode: 'U+1F42B', category: 'animals', keywords: ['双峰驼', '骆驼', 'bactrian'] },
    { emoji: '🦙', name: '羊驼', unicode: 'U+1F999', category: 'animals', keywords: ['羊驼', '草泥马', 'llama'] },
    { emoji: '🐒', name: '猿', unicode: 'U+1F412', category: 'animals', keywords: ['猿', '灵长类', 'ape'] },
    { emoji: '🦍', name: '大猩猩', unicode: 'U+1F98D', category: 'animals', keywords: ['大猩猩', '力量', 'gorilla'] },
    { emoji: '🐔', name: '鸡', unicode: 'U+1F414', category: 'animals', keywords: ['鸡', '家禽', 'chicken'] },
    { emoji: '🐓', name: '公鸡', unicode: 'U+1F413', category: 'animals', keywords: ['公鸡', '打鸣', 'rooster'] },
    { emoji: '🦃', name: '火鸡', unicode: 'U+1F983', category: 'animals', keywords: ['火鸡', '感恩节', 'turkey'] },
    { emoji: '🦆', name: '鸭子', unicode: 'U+1F986', category: 'animals', keywords: ['鸭子', '水禽', 'duck'] },
    { emoji: '🦅', name: '鹰', unicode: 'U+1F985', category: 'animals', keywords: ['鹰', '猛禽', 'eagle'] },
    { emoji: '🦢', name: '天鹅', unicode: 'U+1F9A2', category: 'animals', keywords: ['天鹅', '优雅', 'swan'] },
    { emoji: '🦉', name: '猫头鹰', unicode: 'U+1F989', category: 'animals', keywords: ['猫头鹰', '夜行', 'owl'] },
    { emoji: '🦩', name: '火烈鸟', unicode: 'U+1F9A9', category: 'animals', keywords: ['火烈鸟', '粉色', 'flamingo'] },
    { emoji: '🦚', name: '孔雀', unicode: 'U+1F99A', category: 'animals', keywords: ['孔雀', '开屏', 'peacock'] },
    { emoji: '🦜', name: '鹦鹉', unicode: 'U+1F99C', category: 'animals', keywords: ['鹦鹉', '说话', 'parrot'] },

    // 食物
    { emoji: '🍎', name: '苹果', unicode: 'U+1F34E', category: 'food', keywords: ['苹果', '水果', 'apple'] },
    { emoji: '🍊', name: '橙子', unicode: 'U+1F34A', category: 'food', keywords: ['橙子', '柑橘', 'orange'] },
    { emoji: '🍋', name: '柠檬', unicode: 'U+1F34B', category: 'food', keywords: ['柠檬', '酸', 'lemon'] },
    { emoji: '🍌', name: '香蕉', unicode: 'U+1F34C', category: 'food', keywords: ['香蕉', '水果', 'banana'] },
    { emoji: '🍉', name: '西瓜', unicode: 'U+1F349', category: 'food', keywords: ['西瓜', '夏天', 'watermelon'] },
    { emoji: '🍇', name: '葡萄', unicode: 'U+1F347', category: 'food', keywords: ['葡萄', '水果', 'grapes'] },
    { emoji: '🍓', name: '草莓', unicode: 'U+1F353', category: 'food', keywords: ['草莓', '水果', 'strawberry'] },
    { emoji: '🫐', name: '蓝莓', unicode: 'U+1FAD0', category: 'food', keywords: ['蓝莓', '浆果', 'blueberries'] },
    { emoji: '🍒', name: '樱桃', unicode: 'U+1F352', category: 'food', keywords: ['樱桃', '水果', 'cherries'] },
    { emoji: '🍑', name: '桃子', unicode: 'U+1F351', category: 'food', keywords: ['桃子', '水果', 'peach'] },
    { emoji: '🥭', name: '芒果', unicode: 'U+1F96D', category: 'food', keywords: ['芒果', '热带水果', 'mango'] },
    { emoji: '🍍', name: '菠萝', unicode: 'U+1F34D', category: 'food', keywords: ['菠萝', '热带水果', 'pineapple'] },
    { emoji: '🥥', name: '椰子', unicode: 'U+1F965', category: 'food', keywords: ['椰子', '热带', 'coconut'] },
    { emoji: '🥝', name: '奇异果', unicode: 'U+1F95D', category: 'food', keywords: ['奇异果', '猕猴桃', 'kiwi'] },
    { emoji: '🍅', name: '番茄', unicode: 'U+1F345', category: 'food', keywords: ['番茄', '西红柿', 'tomato'] },
    { emoji: '🍆', name: '茄子', unicode: 'U+1F346', category: 'food', keywords: ['茄子', '蔬菜', 'eggplant'] },
    { emoji: '🥑', name: '牛油果', unicode: 'U+1F951', category: 'food', keywords: ['牛油果', '鳄梨', 'avocado'] },
    { emoji: '🥦', name: '西兰花', unicode: 'U+1F966', category: 'food', keywords: ['西兰花', '蔬菜', 'broccoli'] },
    { emoji: '🥬', name: '青菜', unicode: 'U+1F96C', category: 'food', keywords: ['青菜', '蔬菜', 'leafy'] },
    { emoji: '🥒', name: '黄瓜', unicode: 'U+1F952', category: 'food', keywords: ['黄瓜', '蔬菜', 'cucumber'] },
    { emoji: '🌶️', name: '辣椒', unicode: 'U+1F336', category: 'food', keywords: ['辣椒', '辣', 'hot'] },
    { emoji: '🫑', name: '青椒', unicode: 'U+1FAD1', category: 'food', keywords: ['青椒', '蔬菜', 'bell'] },
    { emoji: '🌽', name: '玉米', unicode: 'U+1F3BD', category: 'food', keywords: ['玉米', '粮食', 'corn'] },
    { emoji: '🥕', name: '胡萝卜', unicode: 'U+1F955', category: 'food', keywords: ['胡萝卜', '蔬菜', 'carrot'] },
    { emoji: '🥔', name: '土豆', unicode: 'U+1F954', category: 'food', keywords: ['土豆', '薯类', 'potato'] },
    { emoji: '🍠', name: '红薯', unicode: 'U+1F960', category: 'food', keywords: ['红薯', '甘薯', 'sweet'] },
    { emoji: '🥐', name: '蘑菇', unicode: 'U+1F950', category: 'food', keywords: ['蘑菇', '真菌', 'mushroom'] },
    { emoji: '🥜', name: '花生', unicode: 'U+1F95C', category: 'food', keywords: ['花生', '坚果', 'peanuts'] },
    { emoji: '🌰', name: '栗子', unicode: 'U+1F330', category: 'food', keywords: ['栗子', '坚果', 'chestnut'] },

    // 交通工具
    { emoji: '🚗', name: '汽车', unicode: 'U+1F697', category: 'transport', keywords: ['汽车', '私家车', 'car'] },
    { emoji: '🚕', name: '出租车', unicode: 'U+1F695', category: 'transport', keywords: ['出租车', '的士', 'taxi'] },
    { emoji: '🚙', name: '越野车', unicode: 'U+1F699', category: 'transport', keywords: ['越野车', 'SUV', 'pickup'] },
    { emoji: '🚌', name: '公交车', unicode: 'U+1F68C', category: 'transport', keywords: ['公交', '大巴', 'bus'] },
    { emoji: '🚎', name: '警车', unicode: 'U+1F68E', category: 'transport', keywords: ['警车', '警察', 'police'] },
    {
      emoji: '🚑',
      name: '救护车',
      unicode: 'U+1F691',
      category: 'transport',
      keywords: ['救护车', '医疗', 'ambulance']
    },
    { emoji: '🚒', name: '消防车', unicode: 'U+1F692', category: 'transport', keywords: ['消防车', '救火', 'fire'] },
    { emoji: '🚐', name: '校车', unicode: 'U+1F690', category: 'transport', keywords: ['校车', '学生', 'school'] },
    { emoji: '🚚', name: '卡车', unicode: 'U+1F69A', category: 'transport', keywords: ['卡车', '货车', 'truck'] },
    { emoji: '🚛', name: '拖车', unicode: 'U+1F69B', category: 'transport', keywords: ['拖车', '救援', 'tractor'] },
    { emoji: '🏎️', name: '赛车', unicode: 'U+1F3CE', category: 'transport', keywords: ['赛车', '速度', 'racing'] },
    {
      emoji: '🚓',
      name: '警用摩托车',
      unicode: 'U+1F693',
      category: 'transport',
      keywords: ['警摩托', '警察', 'motorcycle']
    },
    {
      emoji: '🏍️',
      name: '摩托车',
      unicode: 'U+1F3CD',
      category: 'transport',
      keywords: ['摩托', '机车', 'motorcycle']
    },
    { emoji: '🛵', name: '踏板车', unicode: 'U+1F5F5', category: 'transport', keywords: ['踏板', '电动车', 'scooter'] },
    { emoji: '🚲', name: '自行车', unicode: 'U+1F6B2', category: 'transport', keywords: ['自行车', '骑行', 'bike'] },
    { emoji: '🛴', name: '滑板车', unicode: 'U+1F6F4', category: 'transport', keywords: ['滑板车', '代步', 'kick'] },
    { emoji: '🛹', name: '滑板', unicode: 'U+1F6F9', category: 'transport', keywords: ['滑板', '运动', 'skateboard'] },
    {
      emoji: '🚁',
      name: '直升机',
      unicode: 'U+1F681',
      category: 'transport',
      keywords: ['直升机', '飞行', 'helicopter']
    },
    { emoji: '🛸', name: 'UFO', unicode: 'U+1F7F8', category: 'transport', keywords: ['UFO', '外星人', 'ufo'] },
    { emoji: '✈️', name: '飞机', unicode: 'U+2708', category: 'transport', keywords: ['飞机', '航空', 'airplane'] },
    { emoji: '🛩️', name: '小飞机', unicode: 'U+1F6E9', category: 'transport', keywords: ['小飞机', '私人', 'small'] },
    { emoji: '🛫', name: '喷气式飞机', unicode: 'U+1F6EB', category: 'transport', keywords: ['喷气机', '客机', 'jet'] },
    { emoji: '🚀', name: '火箭', unicode: 'U+1F680', category: 'transport', keywords: ['火箭', '太空', 'rocket'] },
    {
      emoji: '🛰',
      name: '悬浮列车',
      unicode: 'U+1F6F0',
      category: 'transport',
      keywords: ['悬浮', '列车', 'suspension']
    },
    { emoji: '🚊', name: '渡轮', unicode: 'U+1F6A0', category: 'transport', keywords: ['渡轮', '轮船', 'ferry'] },
    { emoji: '🚤', name: '汽艇', unicode: 'U+1F6A4', category: 'transport', keywords: ['汽艇', '快艇', 'speedboat'] },
    { emoji: '⛵', name: '帆船', unicode: 'U+26F5', category: 'transport', keywords: ['帆船', '风帆', 'sailboat'] },
    { emoji: '🚥', name: '锚', unicode: 'U+1F6A5', category: 'transport', keywords: ['锚', '停泊', 'anchor'] },
    { emoji: '⚓', name: '船锚', unicode: 'U+2693', category: 'transport', keywords: ['船锚', '固定', 'anchor'] },
    { emoji: '🛶', name: '救援船', unicode: 'U+1F6F6', category: 'transport', keywords: ['救援', '救生', 'rescue'] },
    { emoji: '🚡', name: '吊车', unicode: 'U+1F6A1', category: 'transport', keywords: ['吊车', '起重', 'crane'] },
    {
      emoji: '🚠',
      name: '轮式装载机',
      unicode: 'U+1F6A3',
      category: 'transport',
      keywords: ['装载机', '工程', 'tractor']
    },
    { emoji: '🚇', name: '缆车', unicode: 'U+1F687', category: 'transport', keywords: ['缆车', '索道', 'cable'] },
    { emoji: '🚈', name: '空中缆车', unicode: 'U+1F688', category: 'transport', keywords: ['空中', '缆车', 'aerial'] },
    {
      emoji: '🚉',
      name: '登山缆车',
      unicode: 'U+1F689',
      category: 'transport',
      keywords: ['登山', '缆车', 'mountain']
    },

    // 活动运动
    { emoji: '⚽', name: '足球', unicode: 'U+26BD', category: 'sports', keywords: ['足球', '运动', 'soccer'] },
    { emoji: '🏀', name: '篮球', unicode: 'U+1F4C0', category: 'sports', keywords: ['篮球', 'NBA', 'basketball'] },
    { emoji: '🏈', name: '橄榄球', unicode: 'U+1F3C8', category: 'sports', keywords: ['橄榄球', 'NFL', 'football'] },
    { emoji: '⚾', name: '棒球', unicode: 'U+26BE', category: 'sports', keywords: ['棒球', 'MLB', 'baseball'] },
    { emoji: '🥎', name: '垒球', unicode: 'U+1F94E', category: 'sports', keywords: ['垒球', '球类', 'softball'] },
    { emoji: '🎾', name: '网球', unicode: 'U+1F3BE', category: 'sports', keywords: ['网球', '球拍', 'tennis'] },
    { emoji: '🏐', name: '排球', unicode: 'U+1F3D0', category: 'sports', keywords: ['排球', '沙滩', 'volleyball'] },
    { emoji: '🏉', name: '羽毛球', unicode: 'U+1F3C9', category: 'sports', keywords: ['羽毛球', '球拍', 'badminton'] },
    { emoji: '🏸', name: '乒乓球', unicode: 'U+1F3D8', category: 'sports', keywords: ['乒乓球', '国球', 'ping'] },
    { emoji: '🥏', name: '板球', unicode: 'U+1F94F', category: 'sports', keywords: ['板球', '球类', 'cricket'] },
    { emoji: '🎱', name: '台球', unicode: 'U+1F3B1', category: 'sports', keywords: ['台球', '桌球', 'pool'] },
    { emoji: '🪀', name: '悠悠球', unicode: 'U+1FA80', category: 'sports', keywords: ['悠悠球', '玩具', 'yo'] },
    { emoji: '🏓', name: '风筝', unicode: 'U+1F3D3', category: 'sports', keywords: ['风筝', '放飞', 'kite'] },
    { emoji: '🏹', name: '飞镖', unicode: 'U+1F3F9', category: 'sports', keywords: ['飞镖', '靶子', 'darts'] },
    { emoji: '🥍', name: '飞盘', unicode: 'U+1F94D', category: 'sports', keywords: ['飞盘', '投掷', 'frisbee'] },
    { emoji: '🏹', name: '回旋镖', unicode: 'U+1F3F9', category: 'sports', keywords: ['回旋镖', '投掷', 'boomerang'] },
    { emoji: '🎣', name: '钓鱼', unicode: 'U+1F3A3', category: 'sports', keywords: ['钓鱼', '鱼竿', 'fishing'] },
    { emoji: '🤿', name: '拳击', unicode: 'U+1F93F', category: 'sports', keywords: ['拳击', '拳套', 'boxing'] },
    { emoji: '🥊', name: '拳击手套', unicode: 'U+1F94A', category: 'sports', keywords: ['拳套', '拳击', 'gloves'] },
    { emoji: '🥋', name: '武术', unicode: 'U+1F94B', category: 'sports', keywords: ['武术', '功夫', 'martial'] },
    { emoji: '🥌', name: '空手道', unicode: 'U+1F94C', category: 'sports', keywords: ['空手道', '武术', 'karate'] },
    { emoji: '🏹', name: '泰拳', unicode: 'U+1F3F9', category: 'sports', keywords: ['泰拳', '格斗', 'muay'] },
    { emoji: '🤸', name: '体操', unicode: 'U+1F938', category: 'sports', keywords: ['体操', '平衡', 'cartwheel'] },
    { emoji: '🤼', name: '篮球转动', unicode: 'U+1F93C', category: 'sports', keywords: ['篮球', '转动', 'ball'] },
    { emoji: '🤽', name: '手球', unicode: 'U+1F93D', category: 'sports', keywords: ['手球', '球类', 'handball'] },
    {
      emoji: '🤾',
      name: '羽毛球转动',
      unicode: 'U+1F93E',
      category: 'sports',
      keywords: ['羽毛球', '转动', 'shuttle']
    },
    { emoji: '🥅', name: '冰球', unicode: 'U+1F945', category: 'sports', keywords: ['冰球', '冰上', 'hockey'] },
    { emoji: '🏒', name: '曲棍球', unicode: 'U+1F3D2', category: 'sports', keywords: ['曲棍球', '球棍', 'field'] },
    { emoji: '🥍', name: '高尔夫', unicode: 'U+1F94D', category: 'sports', keywords: ['高尔夫', '球杆', 'golf'] },
    { emoji: '🏌', name: '旗杆', unicode: 'U+1F3CC', category: 'sports', keywords: ['旗杆', '高尔夫', 'flag'] },
    { emoji: '🏇', name: '终点旗', unicode: 'U+1F3C7', category: 'sports', keywords: ['终点', '旗帜', 'checkered'] }
  ])

  // 计算属性
  const categories = computed(() => [
    { label: '全部', value: '', count: allEmojis.value.length },
    { label: '面部表情', value: 'faces', count: allEmojis.value.filter(e => e.category === 'faces').length },
    { label: '手势符号', value: 'gestures', count: allEmojis.value.filter(e => e.category === 'gestures').length },
    { label: '动物', value: 'animals', count: allEmojis.value.filter(e => e.category === 'animals').length },
    { label: '食物', value: 'food', count: allEmojis.value.filter(e => e.category === 'food').length },
    { label: '交通工具', value: 'transport', count: allEmojis.value.filter(e => e.category === 'transport').length },
    { label: '运动活动', value: 'sports', count: allEmojis.value.filter(e => e.category === 'sports').length }
  ])

  const filteredEmojis = computed(() => {
    let filtered = allEmojis.value

    // 分类过滤
    if (selectedCategory.value) {
      filtered = filtered.filter(emoji => emoji.category === selectedCategory.value)
    }

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        emoji =>
          emoji.name.toLowerCase().includes(query) ||
          emoji.emoji.includes(query) ||
          emoji.keywords.some(keyword => keyword.toLowerCase().includes(query))
      )
    }

    return filtered
  })

  const paginatedEmojis = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredEmojis.value.slice(start, end)
  })

  const totalCopied = computed(() => copyHistory.value.length)

  // 方法
  const copyToClipboard = async (emoji: string, name: string = '') => {
    try {
      await navigator.clipboard.writeText(emoji)

      // 添加到历史记录
      copyHistory.value.push({
        emoji,
        name: name || '表情符号',
        timestamp: Date.now()
      })

      // 限制历史记录数量
      if (copyHistory.value.length > 50) {
        copyHistory.value = copyHistory.value.slice(-50)
      }

      // 保存到localStorage
      localStorage.setItem('emoji-history', JSON.stringify(copyHistory.value))

      // 显示复制成功效果
      recentlyCopied.value = emoji
      setTimeout(() => {
        recentlyCopied.value = ''
      }, 1000)

      ElMessage.success(`已复制 ${emoji}`)
    } catch (err) {
      ElMessage.error('复制失败，请手动复制')
      console.error('复制失败:', err)
    }
  }

  const clearSearch = () => {
    searchQuery.value = ''
    currentPage.value = 1
  }

  const clearHistory = () => {
    copyHistory.value = []
    localStorage.removeItem('emoji-history')
    ElMessage.success('历史记录已清空')
  }

  const isFavorite = (emoji: string) => {
    return favorites.value.includes(emoji)
  }

  const toggleFavorite = (emoji: string) => {
    const index = favorites.value.indexOf(emoji)
    if (index > -1) {
      favorites.value.splice(index, 1)
    } else {
      favorites.value.push(emoji)
    }
    localStorage.setItem('emoji-favorites', JSON.stringify(favorites.value))
  }

  const getCategoryLabel = (category: string) => {
    const cat = categories.value.find(c => c.value === category)
    return cat ? cat.label : category
  }

  const showEmojiDetail = (emoji: Emoji) => {
    selectedEmoji.value = emoji
    detailDialogVisible.value = true
  }

  const showContextMenu = (emoji: Emoji, event: MouseEvent) => {
    contextEmoji.value = emoji
    contextMenuVisible.value = true
    // 在下一个事件循环中设置菜单位置
    setTimeout(() => {
      const menu = document.querySelector('.el-dropdown-menu') as HTMLElement
      if (menu && event) {
        menu.style.position = 'fixed'
        menu.style.left = `${event.clientX}px`
        menu.style.top = `${event.clientY}px`
      }
    }, 0)
  }

  const handleContextMenuCommand = (command: string) => {
    if (!contextEmoji.value) return

    switch (command) {
      case 'copy':
        copyToClipboard(contextEmoji.value.emoji, contextEmoji.value.name)
        break
      case 'copy-unicode':
        copyToClipboard(contextEmoji.value.unicode, 'Unicode代码')
        break
      case 'favorite':
        toggleFavorite(contextEmoji.value.emoji)
        break
      case 'detail':
        showEmojiDetail(contextEmoji.value)
        break
    }

    contextMenuVisible.value = false
  }

  const handleSizeChange = (newSize: number) => {
    pageSize.value = newSize
    currentPage.value = 1
  }

  const handleCurrentChange = (newPage: number) => {
    currentPage.value = newPage
  }

  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    document.documentElement.classList.toggle('dark', isDarkMode.value)
  }

  // 生命周期
  onMounted(() => {
    // 加载历史记录
    const savedHistory = localStorage.getItem('emoji-history')
    if (savedHistory) {
      try {
        copyHistory.value = JSON.parse(savedHistory)
      } catch (e) {
        console.error('加载历史记录失败:', e)
      }
    }

    // 加载收藏
    const savedFavorites = localStorage.getItem('emoji-favorites')
    if (savedFavorites) {
      try {
        favorites.value = JSON.parse(savedFavorites)
      } catch (e) {
        console.error('加载收藏失败:', e)
      }
    }

    // 点击其他地方关闭右键菜单
    document.addEventListener('click', () => {
      contextMenuVisible.value = false
    })
  })

  // 监听右键菜单显示状态
  watch(contextMenuVisible, visible => {
    if (!visible) {
      contextEmoji.value = null
    }
  })
</script>

<style scoped>
  .emoji-viewer {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .emoji-container {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2 {
    margin: 0;
    color: #303133;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .search-section {
    margin-bottom: 20px;
  }

  .search-input {
    margin-bottom: 16px;
  }

  .filter-section {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .category-select,
  .skin-tone-select {
    min-width: 150px;
  }

  .copy-history {
    margin-bottom: 20px;
    padding: 16px;
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
  }

  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-weight: bold;
    color: #606266;
  }

  .history-items {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .history-item {
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 18px;
  }

  .history-item:hover {
    transform: scale(1.1);
    background-color: #409eff;
    color: white;
  }

  .stats-section {
    margin-bottom: 20px;
  }

  .loading-container {
    margin: 20px 0;
  }

  .emoji-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 4px;
    margin: 0 0;
  }

  .emoji-item {
    background: white;
    border: 2px solid #e4e7ed;
    border-radius: 12px;
    padding: 4px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .emoji-item:hover {
    border-color: #409eff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .emoji-item.favorite {
    border-color: #f56c6c;
    background-color: #fef0f0;
  }

  .emoji-item.copied {
    background-color: #f0f9ff;
    border-color: #409eff;
  }

  .emoji-display {
    font-size: 32px;
    margin-bottom: 8px;
    line-height: 1;
  }

  .emoji-name {
    font-size: 12px;
    color: #606266;
    margin-bottom: 8px;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-grow: 1;
  }

  .emoji-actions {
    display: flex;
    justify-content: center;
    gap: 6px;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  .emoji-item:hover .emoji-actions {
    opacity: 1;
  }

  .pagination-section {
    display: flex;
    justify-content: center;
    margin-top: 30px;
  }

  .emoji-detail {
    text-align: center;
  }

  .detail-emoji {
    font-size: 64px;
    margin-bottom: 20px;
  }

  .detail-info {
    text-align: left;
  }

  .keyword-tag {
    margin-right: 8px;
    margin-bottom: 4px;
  }

  /* 深色模式样式 */
  :global(.dark) .emoji-viewer {
    background-color: #1a1a1a;
    color: #ffffff;
  }

  :global(.dark) .emoji-item {
    background: #2d2d2d;
    border-color: #4c4d4f;
    color: #ffffff;
  }

  :global(.dark) .emoji-item:hover {
    border-color: #409eff;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  }

  :global(.dark) .emoji-item.favorite {
    background: #4a2c2c;
    border-color: #f56c6c;
  }

  :global(.dark) .copy-history {
    background: #2d2d2d;
    border-color: #4c4d4f;
  }

  :global(.dark) .history-header {
    color: #c0c4cc;
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .emoji-viewer {
      padding: 10px;
    }

    .filter-section {
      flex-direction: column;
    }

    .category-select,
    .skin-tone-select {
      width: 100%;
    }

    .emoji-grid {
      grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
      gap: 8px;
    }

    .emoji-item {
      min-height: 120px;
      padding: 8px;
    }

    .emoji-display {
      font-size: 24px;
    }

    .header-actions {
      flex-direction: column;
      gap: 8px;
    }
  }

  @media (max-width: 480px) {
    .emoji-grid {
      grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
      gap: 6px;
    }

    .emoji-item {
      min-height: 100px;
      padding: 6px;
    }

    .emoji-display {
      font-size: 20px;
    }

    .emoji-name {
      font-size: 10px;
    }

    .emoji-actions {
      gap: 4px;
    }
  }

  /* 动画效果 */
  .emoji-item {
    animation: fadeInUp 0.3s ease-out;
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* 右键菜单样式 */
  .el-dropdown-menu {
    z-index: 9999;
  }
</style>
