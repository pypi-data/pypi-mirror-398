use crate::runnable::CompilerType;

pub const COUNT_SCRATCH: u8 = 14;

#[derive(Debug, Clone, Copy)]
pub struct Config {
    status: u32,
}

impl Config {
    const USE_SIMD: u32 = 0x01;
    const USE_THREADS: u32 = 0x02;
    const CSE: u32 = 0x04;
    const FASTMATH: u32 = 0x08;
    const SANITIZE: u32 = 0x10;
    const OPT_LEVEL_MASK: u32 = 0x0f00;
    const OPT_LEVEL_SHIFT: usize = 8;

    const BYTECODE: u32 = 0x01 << 16;
    const DEBUG: u32 = 0x02 << 16;
    const SSE: u32 = 0x04 << 16;
    const AVX: u32 = 0x08 << 16;
    const AARCH64: u32 = 0x10 << 16;
    const RISCV: u32 = 0x20 << 16;
    const WINDOWS: u32 = 0x80 << 16;

    pub fn new(ty: CompilerType, opt: u32) -> Config {
        let mut extra: u32 = match ty {
            CompilerType::ByteCode => Self::BYTECODE,
            CompilerType::Amd => {
                if Self::supports_avx() {
                    Self::AVX
                } else {
                    Self::SSE
                }
            }
            CompilerType::AmdAVX => Self::AVX,
            CompilerType::AmdSSE => Self::SSE,
            CompilerType::Arm => Self::AARCH64,
            CompilerType::RiscV => Self::RISCV,
            CompilerType::Native | CompilerType::Debug => {
                if Self::supports_amd64() && Self::supports_avx() {
                    Self::AVX
                } else if Self::supports_amd64() && !Self::supports_avx() {
                    Self::SSE
                } else if Self::supports_arm64() {
                    Self::AARCH64
                } else if Self::supports_riscv64() {
                    Self::RISCV
                } else {
                    Self::BYTECODE
                }
            }
        };

        if matches!(ty, CompilerType::Debug) {
            extra |= Self::DEBUG;
        }

        if cfg!(target_family = "windows") {
            extra |= Self::WINDOWS;
        }

        Config {
            status: (opt as u32) | extra,
        }
    }

    fn bit(&self, mask: u32) -> bool {
        self.status & mask != 0
    }

    pub fn cross_compiled(&self) -> bool {
        (self.bit(Self::AVX) && !Self::supports_avx())
            || (self.bit(Self::SSE) && !Self::supports_amd64())
            || (self.bit(Self::AARCH64) && !Self::supports_arm64())
            || (self.bit(Self::RISCV) && !Self::supports_riscv64())
    }

    pub fn supports_amd64() -> bool {
        cfg!(target_arch = "x86_64")
    }

    pub fn supports_arm64() -> bool {
        cfg!(target_arch = "aarch64")
    }

    pub fn supports_riscv64() -> bool {
        cfg!(target_arch = "riscv64")
    }

    pub fn supports_avx() -> bool {
        #[cfg(target_arch = "x86_64")]
        return is_x86_feature_detected!("avx");
        #[cfg(not(target_arch = "x86_64"))]
        return false;
    }

    pub fn use_simd(&self) -> bool {
        self.bit(Self::USE_SIMD) && self.bit(Self::AVX)
    }

    pub fn use_threads(&self) -> bool {
        self.bit(Self::USE_THREADS)
    }

    pub fn fast_math(&self) -> bool {
        self.bit(Self::FASTMATH)
    }

    pub fn fast_count(&self) -> usize {
        if self.bit(Self::BYTECODE) {
            0
        } else if (self.bit(Self::AVX) || self.bit(Self::SSE)) && self.bit(Self::WINDOWS) {
            4
        } else {
            8
        }
    }

    pub fn opt_level(&self) -> u8 {
        let level: u8 = ((self.status & Self::OPT_LEVEL_MASK) >> Self::OPT_LEVEL_SHIFT) as u8;
        if self.bit(Self::SSE) && self.bit(Self::SANITIZE) {
            0
        } else {
            level
        }
    }

    pub fn compile_sse(&self) -> bool {
        self.bit(Self::SSE)
    }

    pub fn compile_avx(&self) -> bool {
        self.bit(Self::AVX)
    }

    pub fn compile_arm(&self) -> bool {
        self.bit(Self::AARCH64)
    }

    pub fn compile_riscv(&self) -> bool {
        self.bit(Self::RISCV)
    }

    pub fn compile_bytecode(&self) -> bool {
        self.bit(Self::BYTECODE)
    }

    pub fn compile_debug(&self) -> bool {
        self.bit(Self::DEBUG)
    }
}
