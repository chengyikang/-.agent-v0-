/**
 * 用户身份管理 Hook
 * 处理用户创建、验证和状态管理
 */

import { useState, useEffect, useRef } from 'react'
import { User, UseUserReturn } from '@/types'
import { createUser, getUserProfile } from '@/services/api'

const STORAGE_KEY = 'qingxi_user_id'

export function useUser(): UseUserReturn {
  const [userId, setUserId] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const initRef = useRef(false)

  const validateUser = async (id: string): Promise<boolean> => {
    try {
      const profile = await getUserProfile(id)
      if (profile && profile.id) {
        setUser(profile)
        setUserId(id)
        return true
      }
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY)
      }
      return false
    } catch (err) {
      console.error('验证用户失败:', err)
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY)
      }
      return false
    }
  }

  const createNewUser = async (): Promise<boolean> => {
    try {
      setError(null)

      const result = await createUser()

      if (!result || !result.user_id) {
        setError('创建用户返回数据异常')
        return false
      }

      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, result.user_id)
      }

      try {
        const profile = await getUserProfile(result.user_id)
        if (profile) {
          setUser(profile)
        }
      } catch {
        setUser({
          id: result.user_id,
          nickname: result.nickname || null,
          created_at: new Date().toISOString(),
          last_active_at: new Date().toISOString()
        })
      }

      setUserId(result.user_id)
      return true
    } catch (err) {
      console.error('创建用户失败:', err)
      setError('无法创建用户，请刷新页面重试')
      return false
    }
  }

  useEffect(() => {
    if (initRef.current) return
    initRef.current = true

    const initUser = async () => {
      if (typeof window === 'undefined') {
        setLoading(false)
        return
      }

      try {
        const storedUserId = localStorage.getItem(STORAGE_KEY)

        if (storedUserId && storedUserId !== 'undefined' && storedUserId !== 'null') {
          const isValid = await validateUser(storedUserId)
          if (!isValid) {
            await createNewUser()
          }
        } else {
          await createNewUser()
        }
      } catch (err) {
        console.error('用户初始化异常:', err)
        setError('初始化失败，请刷新页面')
      } finally {
        setLoading(false)
      }
    }

    initUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    userId,
    user,
    loading,
    error
  }
}